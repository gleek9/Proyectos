import unittest

from backend.app.agent.collector import MatchDataCollector
from backend.app.agent.scraper import SportsWebScraper
from backend.app.analytics.backtest import run_walk_forward_backtest
from backend.app.db import (
    HistoricalMatch,
    MatchTelemetryCache,
    RefereeCache,
    SessionLocal,
    TeamStatsCache,
)
from backend.app.schemas.match import HeadToHeadStats, MatchRawFeatures, TeamFormStats
from backend.app.services.league_database import league_db


class TestKatakuriV5Paso1DataAndCLV(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()
        self._test_event_id = "unit_test_v50_p1_event"
        self._test_ref_name = "Unit Test Referee v50"

    def tearDown(self):
        try:
            self.db.query(MatchTelemetryCache).filter(
                MatchTelemetryCache.source_event_id == self._test_event_id
            ).delete()
            self.db.query(RefereeCache).filter(
                RefereeCache.name == self._test_ref_name
            ).delete()
            self.db.commit()
        except Exception:
            self.db.rollback()
        finally:
            self.db.close()

    def test_01_full_csv_columns_and_referee_cache_persisted(self):
        total_hm = self.db.query(HistoricalMatch).count()
        self.assertGreaterEqual(total_hm, 7000)

        with_shots = self.db.query(HistoricalMatch).filter(HistoricalMatch.home_shots != None).count()
        with_ht = self.db.query(HistoricalMatch).filter(HistoricalMatch.ht_home_goals != None).count()
        with_ps_open = self.db.query(HistoricalMatch).filter(HistoricalMatch.ps_open_home_odds != None).count()
        with_ps_close = self.db.query(HistoricalMatch).filter(HistoricalMatch.ps_close_home_odds != None).count()
        with_o25 = self.db.query(HistoricalMatch).filter(HistoricalMatch.p_over_25_odds != None).count()

        self.assertGreater(with_shots, 6500)
        self.assertGreater(with_ht, 6500)
        self.assertGreater(with_ps_open, 6500)
        self.assertGreater(with_ps_close, 6500)
        self.assertGreater(with_o25, 6500)

        tsc_shots = self.db.query(TeamStatsCache).filter(TeamStatsCache.avg_shots_for != None).count()
        self.assertGreater(tsc_shots, 120)

        ref_count = self.db.query(RefereeCache).count()
        self.assertGreaterEqual(ref_count, 20)

    def test_02_league_db_propagates_extended_team_metrics(self):
        raw = league_db.get_match_raw_features("Arsenal", "Liverpool", "Premier League")
        self.assertIsNotNone(raw)
        self.assertIsNotNone(raw.home_stats.avg_shots_for)
        self.assertIsNotNone(raw.home_stats.avg_fouls_for)
        self.assertIsNotNone(raw.home_stats.ht_goal_diff_avg)
        self.assertGreater(raw.home_stats.avg_shots_for, 5.0)
        self.assertTrue(any(m.shots_for is not None for m in raw.home_stats.last_matches))

    def test_03_incremental_sofascore_cache_and_collector_enrichment(self):
        sc = SportsWebScraper()
        telem = {
            "home_team": "Arsenal",
            "away_team": "Chelsea",
            "match_date": "2026-11-12",
            "xg_home": 2.14,
            "xg_away": 0.87,
            "corners": 9,
            "referee_name": self._test_ref_name,
            "referee_avg_cards": 4.65,
            "referee_stats": {
                "name": self._test_ref_name,
                "yellow_cards": 85,
                "red_cards": 4,
                "yellow_red_cards": 2,
                "games": 20,
                "avg_cards_per_game": 4.75,
            },
            "missing_players": {
                "home": ["Bukayo Saka (injured)"],
                "away": ["Cole Palmer (suspended)"],
            },
            "lineups": {
                "home": ["David Raya", "William Saliba"],
                "away": ["Robert Sanchez", "Levi Colwill"],
            },
        }
        ok = sc.persist_incremental_sofascore_cache(self._test_event_id, telem)
        self.assertTrue(ok)

        row = self.db.query(MatchTelemetryCache).filter(
            MatchTelemetryCache.source_event_id == self._test_event_id
        ).first()
        self.assertIsNotNone(row)
        self.assertAlmostEqual(row.xg_home, 2.14, places=2)
        self.assertEqual(row.referee_name, self._test_ref_name)

        ref_row = self.db.query(RefereeCache).filter(RefereeCache.name == self._test_ref_name).first()
        self.assertIsNotNone(ref_row)
        self.assertEqual(ref_row.source, "sofascore")
        self.assertAlmostEqual(ref_row.avg_cards_per_game, 4.75, places=2)

        raw = MatchRawFeatures(
            home_team="Arsenal",
            away_team="Chelsea",
            competition="Premier League",
            home_stats=TeamFormStats(team_name="Arsenal"),
            away_stats=TeamFormStats(team_name="Chelsea"),
            h2h=HeadToHeadStats(),
        )
        MatchDataCollector._apply_url_telemetry(raw, telem)
        self.assertAlmostEqual(raw.live_xg_home, 2.14, places=2)
        self.assertAlmostEqual(raw.live_xg_away, 0.87, places=2)
        self.assertEqual(raw.referee_name, self._test_ref_name)
        self.assertIn("Bukayo Saka (injured)", raw.home_stats.key_absences)
        self.assertIn("Cole Palmer (suspended)", raw.away_stats.key_absences)

    def test_04_walk_forward_opening_vs_closing_and_clv(self):
        res_open = run_walk_forward_backtest(n_matches=60, edge_threshold=0.04, odds_source="opening")
        wf_open = res_open.get("walk_forward_simulation", {})
        self.assertEqual(wf_open.get("odds_source"), "opening")
        self.assertIn("pinnacle_closing_benchmark", wf_open)
        self.assertIn("opening_vs_closing_comparison", wf_open)
        vb = wf_open.get("value_betting", {})
        self.assertIn("avg_clv_pct", vb)
        self.assertIn("clv_beat_rate_pct", vb)

        cmp_blk = wf_open["opening_vs_closing_comparison"]
        self.assertIn("bet365_opening", cmp_blk)
        self.assertIn("pinnacle_opening", cmp_blk)
        self.assertIn("pinnacle_closing", cmp_blk)
        self.assertIsNotNone(cmp_blk["pinnacle_closing"].get("market_rps_mean"))


if __name__ == "__main__":
    unittest.main()

