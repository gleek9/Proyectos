import json
from datetime import datetime
from sqlalchemy.orm import Session
from models import Profile, AnalysisReport, ScriptProposal
from services.apify_service import apify_service
from services.media_extractor import media_extractor
from services.gemini_service import gemini_service

def run_analysis_pipeline(profile: Profile, db: Session) -> AnalysisReport:
    """
    Orquesta el pipeline completo de análisis:
    1. Radiografía del cliente (Brand Voice).
    2. Caza de virales de competidores (Top 3 Reels).
    3. Extracción de audio / transcripción multimodal con Gemini 3.0.
    4. Generación de 3 propuestas de guiones estructurados (Título, Escaleta, Guion).
    5. Persistencia en base de datos local SQLite.
    """
    # Fase 1: Radiografía de la voz del cliente
    competitor_urls = profile.get_competitor_urls_list()
    client_voice = apify_service.extract_client_voice(
        client_url=profile.client_instagram_url,
        client_name=profile.client_name,
        category=profile.category
    )
    profile.brand_voice_summary = client_voice

    # Fase 2: Extracción de los 3 mejores virales de la competencia
    top_virals = apify_service.extract_top_viral_reels(
        competitor_urls=competitor_urls,
        category=profile.category
    )

    # Fase 3: Procesamiento multimedia de los Reels (audio y transcripción)
    processed_reels = []
    for item in top_virals:
        video_url = item.get("video_url")
        reel_url = item.get("url")
        caption = item.get("caption", "")
        transcript = caption

        # Intentar extraer audio si existe URL directa de video
        if video_url:
            audio_result = media_extractor.download_reel_audio(video_url)
            if audio_result:
                audio_bytes, mime_type = audio_result
                try:
                    ai_transcript = gemini_service.transcribe_and_analyze_audio(audio_bytes, mime_type)
                    if ai_transcript:
                        transcript = ai_transcript
                except Exception:
                    pass

        processed_reels.append({
            "url": reel_url,
            "competitor_username": item.get("owner_username", "competidor"),
            "views": item.get("views", 0),
            "likes": item.get("likes", 0),
            "comments": item.get("comments", 0),
            "caption": caption,
            "transcript_or_hook": transcript
        })

    # Fase 4: Creación de los 3 guiones e ingeniería inversa con Gemini 3.0
    proposals_data = gemini_service.generate_script_proposals(
        client_name=profile.client_name,
        category=profile.category,
        brand_voice=client_voice,
        competitor_reels=processed_reels
    )

    # Fallback de seguridad en caso de fallo en el formato de Gemini
    if not proposals_data or len(proposals_data) < 3:
        proposals_data = _build_default_proposals(profile.client_name, profile.category, processed_reels)

    # Fase 5: Persistencia en SQLite
    report = AnalysisReport(
        profile_id=profile.id,
        summary=f"Análisis estratégico basado en {len(processed_reels)} virales de la competencia para la categoría '{profile.category}'.",
        created_at=datetime.utcnow()
    )
    db.add(report)
    db.flush()  # Para obtener report.id

    for prop in proposals_data[:3]:
        timeline = _ensure_unified_timeline(
            prop.get("escalation_timeline", []),
            prop.get("full_script", "")
        )
        full_script = _format_unified_script(timeline) if timeline else (prop.get("full_script") or "Guion en generación.")
        script_item = ScriptProposal(
            report_id=report.id,
            title=prop.get("title", f"Oportunidad Viral para {profile.client_name}"),
            competitor_source_info=prop.get("competitor_source_info", "Inspirado en tendencia viral del sector"),
            virality_badge=prop.get("virality_badge", "Alto impacto"),
            full_script=full_script,
            original_reel_url=prop.get("original_reel_url", ""),
            original_transcript=prop.get("original_transcript", "")
        )
        script_item.set_timeline_list(timeline)
        db.add(script_item)

    db.commit()
    db.refresh(report)
    return report


def _ensure_unified_timeline(timeline: list, fallback_script: str) -> list:
    """Garantiza que cada bloque de la escaleta tenga su texto hablado (spoken_text)."""
    if not timeline:
        return timeline
    missing = [b for b in timeline if not (b.get("spoken_text") or "").strip()]
    if missing and fallback_script:
        chunks = [c.strip() for c in fallback_script.split("\n\n") if c.strip()]
        if len(chunks) < len(timeline):
            sentences = [s.strip() for s in fallback_script.replace("\n", " ").split(". ") if s.strip()]
            step = max(1, len(sentences) // len(timeline))
            chunks = [
                ". ".join(sentences[i * step : (i + 1) * step if i < len(timeline) - 1 else len(sentences)])
                for i in range(len(timeline))
            ]
        for idx, block in enumerate(timeline):
            if not (block.get("spoken_text") or "").strip() and idx < len(chunks):
                block["spoken_text"] = chunks[idx]
    return timeline


def _format_unified_script(timeline: list) -> str:
    """Construye un guion unificado legible combinando tiempos, dirección visual y texto hablado."""
    parts = []
    for block in timeline:
        tr = block.get("time_range", "00:00")
        phase = block.get("phase", "")
        desc = block.get("description", "")
        screen = block.get("on_screen_text")
        spoken = block.get("spoken_text", "")
        header = f"[{tr} | {phase}]"
        meta = f"(Visual: {desc}" + (f" · Texto en pantalla: \"{screen}\"" if screen else "") + ")"
        parts.append(f"{header}\n{meta}\n{spoken}".strip())
    return "\n\n".join(parts)


def _build_default_proposals(client_name: str, category: str, processed_reels: list) -> list:
    """Genera propuestas estructuradas de respaldo (60-90s) con hooks virales y cada sección de escaleta unida a su guion."""
    proposals = []
    templates = [
        {
            "archetype": "Contrarian Claim",
            "title": f"Lo que casi nadie corrige en {category} (y te frena cada mes)",
            "hook": f"Todo el mundo cree que el problema en {category} es falta de presupuesto, pero casi siempre es el orden en que ejecutan el primer paso.",
            "on_screen_hook": "El error invisible",
            "context": (
                f"Imagina invertir tiempo, equipo y dinero cada semana esperando resultados constantes, pero saltarte justo la base que decide si tu cliente confía o pasa de largo. "
                f"La mayoría empieza por la oferta o por el precio sin haber dejado claro qué problema específico resuelve hoy, y por eso el mensaje se diluye en los primeros segundos."
            ),
            "rehook": "¡Espera! Antes de cambiar de estrategia o bajar precios, mira dónde se está fugando realmente la atención de tus clientes.",
            "payoff": (
                f"Primero, define en una sola frase qué resultado concreto entregas y para quién es exactamente. "
                f"Segundo, muestra una prueba real, un antes y después o un caso tangible antes de hablar de características técnicas. "
                f"Tercero, elimina los pasos innecesarios entre el primer contacto y la conversación real. "
                f"En {client_name} aplicamos exactamente esta secuencia en {category} para transformar visitas frías en oportunidades calificadas todas las semanas sin improvisar."
            ),
            "cta": "Guarda este video para revisarlo antes de tu próxima grabación y comenta 'GUIA' si quieres que te compartamos la estructura paso a paso.",
            "duration_label": "~75s"
        },
        {
            "archetype": "Mistake / Cost Confession",
            "title": f"3 errores que cuestan caro en {category} (y cómo evitarlos)",
            "hook": f"Si estás buscando resultados consistentes en {category}, repetir este patrón común te puede costar meses de retraso y oportunidades perdidas.",
            "on_screen_hook": "3 errores caros",
            "context": (
                f"Casi todos copian lo que ven en superficie porque parece rápido y fácil de replicar. "
                f"El problema es que lo que funciona para una cuenta con años de posicionamiento quema el alcance y la credibilidad de un negocio que necesita convertir hoy."
            ),
            "rehook": "Pero hay una salida mucho más simple, y empieza por corregir dos decisiones antes de publicar un solo video más.",
            "payoff": (
                f"Error uno: hablarle a todo el mundo con frases genéricas que no generan urgencia ni identificación inmediata. "
                f"Error dos: explicar diez ideas distintas en un mismo contenido en lugar de profundizar en una sola objeción real del cliente. "
                f"Error tres: cerrar sin una dirección clara. Cuando conviertes cada duda frecuente en un ejemplo práctico de sesenta segundos, como hacemos en {client_name}, tu audiencia entiende tu valor desde el primer minuto."
            ),
            "cta": "Comparte este video con alguien de tu equipo que necesite verlo hoy y comenta 'PLAN' para enviarte el checklist completo.",
            "duration_label": "~80s"
        },
        {
            "archetype": "Curiosity Gap",
            "title": f"El método silencioso que está cambiando {category}",
            "hook": f"Nadie te explica el detalle de diez segundos que separa una estrategia promedio en {category} de una que convierte todos los días.",
            "on_screen_hook": "El detalle clave",
            "context": (
                f"Puedes tener el mejor servicio o producto de tu ciudad, pero si los primeros cuatro segundos no abren una pregunta clara en la mente del espectador, nadie se queda a escuchar tu propuesta. "
                f"La atención no se pide con saludos largos ni presentaciones lentas; se gana planteando un contraste real."
            ),
            "rehook": "Y aquí está lo interesante: no necesitas publicar el doble ni gastar más, necesitas cambiar el orden en que cuentas tu historia.",
            "payoff": (
                f"Empieza mostrando el resultado o el cuello de botella real. Luego explica por qué la solución obvia falla, introduce el ajuste clave y demuestra cómo funciona en la práctica. "
                f"Eso es justo lo que implementamos en {client_name}: claridad directa desde el segundo cero para que cada pieza de contenido construya autoridad y confianza."
            ),
            "cta": "Guarda esta estructura para tu siguiente guion y síguenos para ver el desglose del próximo caso real.",
            "duration_label": "~70s"
        }
    ]

    for i, t in enumerate(templates):
        reel_info = processed_reels[i] if i < len(processed_reels) else {}
        comp = reel_info.get("competitor_username", "competidor")
        views = reel_info.get("views", 150000)
        likes = reel_info.get("likes", 12000)
        views_label = f"{views // 1000}K vistas" if views >= 1000 else f"{views} vistas"
        badge = f"{views_label} • {t['duration_label']}"
        ref_excerpt = (reel_info.get("transcript_or_hook") or "").strip()
        ref_note = (
            f"Referencia de @{comp} ({views_label}, {likes} likes): "
            f"{ref_excerpt[:220] + ('...' if len(ref_excerpt) > 220 else '') if ref_excerpt else 'Estructura de alto contraste y retención aplicada al tono del cliente.'}"
        )

        timeline = [
            {
                "time_range": "00:00 - 00:04",
                "phase": f"Hook · {t['archetype']}",
                "on_screen_text": t["on_screen_hook"],
                "description": "Plano cerrado a cámara con movimiento dinámico inicial y corte seco.",
                "spoken_text": t["hook"]
            },
            {
                "time_range": "00:04 - 00:20",
                "phase": "Contexto y Tensión",
                "on_screen_text": "Por qué pasa esto",
                "description": "Cambio de ángulo o B-roll de apoyo ilustrando el problema real.",
                "spoken_text": t["context"]
            },
            {
                "time_range": "00:20 - 00:36",
                "phase": "Re-Hook y Quiebre",
                "on_screen_text": "Pero espera...",
                "description": "Zoom sutil de énfasis para reiniciar la atención en mitad del video.",
                "spoken_text": t["rehook"]
            },
            {
                "time_range": "00:36 - 01:08",
                "phase": "Payoff y Solución",
                "on_screen_text": "Paso a paso",
                "description": "Cortes cada 3-4 segundos destacando cada clave visualmente en pantalla.",
                "spoken_text": t["payoff"]
            },
            {
                "time_range": "01:08 - 01:20",
                "phase": "Remate y CTA",
                "on_screen_text": "Guarda esto",
                "description": "Plano limpio a cámara con cierre directo y palabra clave visible.",
                "spoken_text": t["cta"]
            }
        ]

        proposals.append({
            "title": t["title"],
            "competitor_source_info": f"Ref: @{comp} ({views_label}) • Hook: {t['archetype']}",
            "virality_badge": badge,
            "original_reel_url": reel_info.get("url", f"https://instagram.com/{comp}"),
            "original_transcript": ref_note,
            "escalation_timeline": timeline,
            "full_script": _format_unified_script(timeline)
        })

    return proposals
