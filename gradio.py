from pathlib import Path
import sys

from gradio_deploy.detector import detect_road_damage


APP_DIR = Path(__file__).resolve().parent


def import_gradio_package():
    """Import the installed package when this file is named gradio.py."""
    original_sys_path = sys.path[:]
    sys.path = [
        entry
        for entry in sys.path
        if Path(entry or ".").resolve() != APP_DIR
    ]
    try:
        import gradio as gradio_package
    finally:
        sys.path = original_sys_path
    return gradio_package


gr = import_gradio_package()


def certainty_label(confidence: float) -> str:
    if confidence >= 0.75:
        return "Strong match"
    if confidence >= 0.5:
        return "Likely match"
    return "Possible match"


def damage_tone(damage_type: str) -> str:
    if damage_type == "Pothole":
        return "pothole"
    if damage_type == "Alligator crack":
        return "surface"
    if damage_type == "Transverse crack":
        return "cross"
    return "long"


def status_html(tone: str, label: str, message: str) -> str:
    return f"""
    <div class="result-status {tone}">
        <span class="status-mark" aria-hidden="true"></span>
        <div>
            <strong>{label}</strong>
            <p>{message}</p>
        </div>
    </div>
    """


def empty_report_html() -> str:
    return """
    <div class="report-empty">
        <div class="road-symbol" aria-hidden="true"><span></span></div>
        <div>
            <h3>No results yet</h3>
            <p>Your detected road damage will appear here.</p>
        </div>
    </div>
    """


def detections_report_html(detections) -> str:
    if not detections:
        return """
        <div class="clear-result">
            <span aria-hidden="true">&#10003;</span>
            <div>
                <h3>No visible damage found</h3>
                <p>Try another photo if the road surface is unclear.</p>
            </div>
        </div>
        """

    cards = []
    visible_detections = detections[:2]
    for detection in visible_detections:
        score = detection.confidence * 100
        cards.append(
            f"""
            <article class="finding-card {damage_tone(detection.damage_type)}">
                <span class="damage-swatch" aria-hidden="true"></span>
                <div class="finding-copy">
                    <h3>{detection.damage_type}</h3>
                    <p>{certainty_label(detection.confidence)}</p>
                    <div class="match-track"><span style="width: {score:.1f}%"></span></div>
                </div>
                <strong>{score:.0f}%</strong>
            </article>
            """
        )

    count = len(detections)
    area_label = "damaged area" if count == 1 else "damaged areas"
    remaining = count - len(visible_detections)
    more_html = (
        f'<p class="more-findings">+{remaining} more marked on the image</p>'
        if remaining > 0
        else ""
    )
    return f"""
    <div class="report-summary">
        <strong>{count}</strong>
        <span>{area_label} found</span>
    </div>
    <div class="report-list">{''.join(cards)}</div>
    {more_html}
    """


def analyze_road_image(image):
    if image is None:
        return (
            None,
            status_html("waiting", "Add a road photo", "Choose an image before checking for damage."),
            empty_report_html(),
        )

    try:
        annotated, detections = detect_road_damage(image)
    except Exception:
        return (
            None,
            status_html("error", "Image could not be checked", "Try a clear JPG or PNG road photo."),
            empty_report_html(),
        )

    if detections:
        count = len(detections)
        label = "Damage found"
        message = f"{count} damaged area{'s' if count != 1 else ''} marked on the road image."
        tone = "damage"
    else:
        label = "No damage found"
        message = "No cracks or potholes were visible in this photo."
        tone = "clear"

    return (
        annotated,
        status_html(tone, label, message),
        detections_report_html(detections),
    )


CSS = """
:root {
    --night: #090b0c;
    --asphalt: #101315;
    --asphalt-soft: #171b1e;
    --road: #22282c;
    --line: #31393e;
    --text: #f5f7f7;
    --muted: #9aa5aa;
    --lane: #ffc23b;
    --inspect: #49c4d2;
    --damage: #ef7457;
    --safe: #55c596;
}

html,
body {
    margin: 0;
    height: 100%;
    min-height: 100%;
    overflow: hidden !important;
    background: var(--night);
}

.gradio-container {
    width: 100vw !important;
    min-width: 100% !important;
    min-height: 100dvh !important;
    padding: 0 !important;
    overflow: hidden !important;
    background: var(--night) !important;
    color: var(--text) !important;
    font-family: "Segoe UI Variable", "Segoe UI", system-ui, sans-serif !important;
    letter-spacing: 0 !important;
}

.gradio-container > .main,
.gradio-container .main,
.gradio-container > div,
.gradio-container .contain,
.gradio-container main,
.gradio-container main > div:first-child {
    width: 100% !important;
    max-width: none !important;
    margin: 0 !important;
    padding: 0 !important;
    gap: 0 !important;
}

.site-header {
    position: relative;
    display: flex;
    align-items: center;
    width: 100vw;
    height: 100px;
    margin: -10px 0 -10px -12px;
    padding: 0 28px;
    overflow: hidden;
    background: var(--night);
    border-bottom: 1px solid var(--line);
}

.site-header:after {
    content: "";
    position: absolute;
    right: 28px;
    bottom: -1px;
    width: 34%;
    height: 4px;
    background: repeating-linear-gradient(
        90deg,
        var(--lane) 0 42px,
        transparent 42px 68px
    );
}

.brand-lockup {
    display: flex;
    align-items: center;
    gap: 15px;
    min-width: 0;
}

.road-logo {
    position: relative;
    width: 52px;
    height: 52px;
    flex: 0 0 52px;
    overflow: hidden;
    background: var(--road);
    border: 1px solid #414a50;
    border-radius: 4px;
}

.road-logo:before,
.road-logo:after,
.road-logo span {
    content: "";
    position: absolute;
    width: 3px;
    height: 13px;
    left: 24px;
    background: var(--lane);
}

.road-logo:before { top: -2px; }
.road-logo span { top: 19px; }
.road-logo:after { bottom: -2px; }

.site-header h1 {
    margin: 0;
    color: var(--text) !important;
    font-family: "Bahnschrift", "Arial Narrow", "Segoe UI", sans-serif;
    font-size: 2.15rem;
    font-weight: 750;
    line-height: 1;
    letter-spacing: 0;
}

.site-header p {
    margin: 6px 0 0;
    color: var(--muted) !important;
    font-size: 1.15rem;
    letter-spacing: 0;
}

.app-main {
    position: relative;
    left: -12px;
    display: grid !important;
    grid-template-columns: minmax(430px, 0.82fr) minmax(660px, 1.45fr) !important;
    width: 100vw !important;
    height: calc(100dvh - 100px);
    min-height: 0 !important;
    margin: 0 !important;
    gap: 0 !important;
    overflow: hidden;
}

.input-panel,
.result-panel {
    min-width: 0 !important;
    height: 100%;
    padding: 28px !important;
    overflow: hidden !important;
    border: 0 !important;
    border-radius: 0 !important;
    box-shadow: none !important;
}

.input-panel {
    flex-flow: column nowrap !important;
    justify-content: flex-start !important;
    background: var(--asphalt) !important;
    border-right: 1px solid var(--line) !important;
}

.result-panel {
    flex-flow: column nowrap !important;
    justify-content: flex-start !important;
    background: var(--asphalt-soft) !important;
}

.panel-heading {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 18px;
    min-height: 76px;
    margin-bottom: 12px;
}

.panel-heading span,
.section-label {
    color: var(--lane) !important;
    font-size: 1rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0;
}

.panel-heading h2 {
    margin: 5px 0 0;
    color: var(--text) !important;
    font-family: "Bahnschrift", "Arial Narrow", "Segoe UI", sans-serif;
    font-size: 1.9rem;
    font-weight: 700;
    letter-spacing: 0;
}

.panel-heading p {
    margin: 7px 0 0;
    color: var(--muted) !important;
    font-size: 1.15rem;
}

.result-heading {
    align-items: center;
}

#source-image,
#result-image {
    flex: 0 0 auto !important;
    overflow: hidden;
    background: #0b0e10 !important;
    border: 1px solid var(--line) !important;
    border-radius: 6px !important;
    box-shadow: none !important;
}

#source-image {
    min-height: max(300px, calc(100dvh - 520px)) !important;
}

#result-image {
    position: relative;
    min-height: max(250px, calc(100dvh - 700px)) !important;
}

#source-image > div,
#source-image .wrap,
#source-image .container,
#source-image .image-container,
#source-image .image-frame,
#source-image [class*="upload"],
#result-image > div,
#result-image .wrap,
#result-image .container,
#result-image .image-container,
#result-image .image-frame {
    background: #0b0e10 !important;
}

#source-image button,
#source-image .wrap *,
#result-image .wrap * {
    color: #c2ccd0 !important;
}

#source-image:hover {
    border-color: var(--lane) !important;
}

#result-image:after {
    content: "";
    position: absolute;
    z-index: 3;
    right: 18px;
    bottom: 18px;
    width: 48px;
    height: 4px;
    pointer-events: none;
    background: repeating-linear-gradient(
        90deg,
        var(--lane) 0 12px,
        transparent 12px 20px
    );
}

.action-row {
    flex: 0 0 62px !important;
    min-height: 62px !important;
    margin: 14px 0 16px !important;
}

#detect-button {
    min-height: 62px !important;
    background: var(--lane) !important;
    color: #151718 !important;
    border: 0 !important;
    border-radius: 6px !important;
    font-size: 1.25rem !important;
    font-weight: 800 !important;
    box-shadow: 0 12px 26px rgba(255, 194, 59, 0.16) !important;
}

#detect-button:hover {
    background: #ffd064 !important;
    transform: translateY(-1px);
}

.damage-types {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 7px;
}

.damage-types div {
    min-width: 0;
    min-height: 52px;
    padding: 12px 8px;
    overflow: hidden;
    background: #0c0f11;
    border: 1px solid #292f33;
    border-radius: 4px;
    color: #c5ced2;
    font-size: 1rem;
    text-align: center;
    white-space: nowrap;
    text-overflow: ellipsis;
}

.damage-types i {
    display: block;
    width: 18px;
    height: 3px;
    margin: 0 auto 7px;
    background: var(--lane);
}

.damage-types div:nth-child(2) i { background: var(--inspect); }
.damage-types div:nth-child(3) i { background: #a28bdd; }
.damage-types div:nth-child(4) i { background: var(--damage); }

.status-output {
    flex: 0 0 auto !important;
    margin-bottom: 14px !important;
}

.result-status {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr);
    align-items: center;
    gap: 12px;
    min-height: 78px;
    padding: 14px 16px;
    background: #0d1113;
    border: 1px solid var(--line);
    border-radius: 6px;
}

.status-mark {
    width: 12px;
    height: 12px;
    background: var(--lane);
    border-radius: 50%;
    box-shadow: 0 0 0 5px rgba(255, 194, 59, 0.12);
}

.result-status.damage .status-mark,
.result-status.error .status-mark {
    background: var(--damage);
    box-shadow: 0 0 0 5px rgba(239, 116, 87, 0.12);
}

.result-status.clear .status-mark {
    background: var(--safe);
    box-shadow: 0 0 0 5px rgba(85, 197, 150, 0.12);
}

.result-status strong {
    color: var(--text);
    font-size: 1.15rem;
}

.result-status p {
    margin: 4px 0 0;
    color: var(--muted);
    font-size: 1rem;
}

.report-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: 16px 0 10px;
}

.report-heading h2 {
    margin: 0;
    color: var(--text);
    font-family: "Bahnschrift", "Arial Narrow", "Segoe UI", sans-serif;
    font-size: 1.35rem;
}

.report-heading span {
    color: var(--muted);
    font-size: 0.95rem;
}

.report-empty,
.clear-result {
    display: flex;
    align-items: center;
    gap: 16px;
    min-height: 112px;
    padding: 18px;
    background: #0d1113;
    border: 1px solid var(--line);
    border-radius: 6px;
}

.report-empty h3,
.report-empty p,
.clear-result h3,
.clear-result p {
    margin: 0;
}

.report-empty h3,
.clear-result h3 {
    color: var(--text);
    font-size: 1.15rem;
}

.report-empty p,
.clear-result p {
    margin-top: 5px;
    color: var(--muted);
    font-size: 0.95rem;
}

.road-symbol {
    position: relative;
    width: 42px;
    height: 52px;
    flex: 0 0 42px;
    overflow: hidden;
    background: var(--road);
    border: 1px solid #3a4348;
    border-radius: 4px;
}

.road-symbol:before,
.road-symbol:after,
.road-symbol span {
    content: "";
    position: absolute;
    left: 19px;
    width: 3px;
    height: 12px;
    background: var(--lane);
}

.road-symbol:before { top: -1px; }
.road-symbol span { top: 20px; }
.road-symbol:after { bottom: -1px; }

.clear-result > span {
    display: grid;
    width: 42px;
    height: 42px;
    flex: 0 0 42px;
    place-items: center;
    color: #07110d;
    background: var(--safe);
    border-radius: 50%;
    font-size: 1.2rem;
    font-weight: 900;
}

.report-summary {
    display: flex;
    align-items: baseline;
    gap: 10px;
    margin-bottom: 10px;
}

.report-summary strong {
    color: var(--lane);
    font-family: "Bahnschrift", "Arial Narrow", "Segoe UI", sans-serif;
    font-size: 1.8rem;
}

.report-summary span {
    color: var(--muted);
    font-size: 1rem;
}

.report-list {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
}

.finding-card {
    display: grid;
    grid-template-columns: 8px minmax(0, 1fr) auto;
    align-items: center;
    gap: 12px;
    min-width: 0;
    padding: 12px;
    background: #0d1113;
    border: 1px solid var(--line);
    border-radius: 5px;
}

.damage-swatch {
    width: 8px;
    height: 38px;
    background: var(--lane);
    border-radius: 2px;
}

.finding-card.cross .damage-swatch { background: var(--inspect); }
.finding-card.surface .damage-swatch { background: #a28bdd; }
.finding-card.pothole .damage-swatch { background: var(--damage); }

.finding-copy {
    min-width: 0;
}

.finding-card h3 {
    margin: 0;
    overflow: hidden;
    color: var(--text);
    font-size: 1.05rem;
    white-space: nowrap;
    text-overflow: ellipsis;
}

.finding-card p {
    margin: 4px 0 0;
    color: var(--muted);
    font-size: 0.9rem;
}

.finding-card > strong {
    color: var(--text);
    font-size: 1rem;
}

.more-findings {
    margin: 10px 0 0;
    color: var(--muted);
    font-size: 0.95rem;
}

.match-track {
    width: 100%;
    height: 3px;
    margin-top: 8px;
    overflow: hidden;
    background: #252c30;
    border-radius: 3px;
}

.match-track span {
    display: block;
    height: 100%;
    background: var(--inspect);
}

.gradio-container button:focus-visible,
.gradio-container input:focus-visible {
    outline: 3px solid rgba(73, 196, 210, 0.4) !important;
    outline-offset: 2px;
}

.gradio-container footer {
    display: none !important;
}

@media (max-width: 980px) {
    .gradio-container {
        overflow: auto !important;
    }

    .site-header {
        margin-left: -10px;
        padding: 0 18px;
    }

    .site-header:after {
        right: 18px;
        width: 28%;
    }

    .app-main {
        left: -10px;
        display: flex !important;
        width: 100% !important;
        height: auto;
        overflow: visible;
    }

    .input-panel,
    .result-panel {
        width: 100% !important;
        height: auto;
        overflow: visible;
    }

    #source-image,
    #result-image {
        min-height: 420px !important;
    }
}

@media (max-width: 600px) {
    .site-header {
        height: 72px;
    }

    .site-header h1 {
        font-size: 1.15rem;
    }

    .site-header p {
        font-size: 0.7rem;
    }

    .site-header:after {
        display: none;
    }

    .input-panel,
    .result-panel {
        padding: 18px !important;
    }

    #source-image,
    #result-image {
        min-height: 320px !important;
    }

    .damage-types,
    .report-list {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

@media (prefers-reduced-motion: reduce) {
    *,
    *:before,
    *:after {
        transition: none !important;
    }
}
"""


theme = gr.themes.Base(
    primary_hue="amber",
    neutral_hue="zinc",
).set(
    body_background_fill="#090b0c",
    block_background_fill="#101315",
    block_border_color="#31393e",
    button_primary_background_fill="#ffc23b",
    button_primary_text_color="#151718",
    body_text_color="#f5f7f7",
    body_text_color_subdued="#9aa5aa",
)


with gr.Blocks(
    title="Road Damage Detector",
    fill_height=True,
    fill_width=True,
) as demo:
    gr.HTML(
        """
        <header class="site-header">
            <div class="brand-lockup">
                <div class="road-logo" aria-hidden="true"><span></span></div>
                <div>
                    <h1>Road Damage Detector</h1>
                    <p>Find cracks and potholes in a road photo.</p>
                </div>
            </div>
        </header>
        """
    )

    with gr.Row(equal_height=False, elem_classes=["app-main"]):
        with gr.Column(scale=4, min_width=430, elem_classes=["input-panel"]):
            gr.HTML(
                """
                <div class="panel-heading">
                    <div>
                        <span>Road photo</span>
                        <h2>Choose an image to inspect</h2>
                        <p>Use a clear view of the road surface.</p>
                    </div>
                </div>
                """
            )

            image_input = gr.Image(
                type="pil",
                label="Road photo",
                show_label=False,
                height="max(300px, calc(100dvh - 520px))",
                sources=["upload", "clipboard"],
                buttons=[],
                placeholder="Drop a road photo here or click to browse",
                elem_id="source-image",
            )

            with gr.Row(elem_classes=["action-row"]):
                detect_button = gr.Button(
                    "Check road image",
                    variant="primary",
                    elem_id="detect-button",
                )

            gr.HTML(
                """
                <div class="section-label">Detects</div>
                <div class="damage-types">
                    <div><i></i>Long cracks</div>
                    <div><i></i>Cross cracks</div>
                    <div><i></i>Surface cracks</div>
                    <div><i></i>Potholes</div>
                </div>
                """
            )

        with gr.Column(scale=7, min_width=660, elem_classes=["result-panel"]):
            gr.HTML(
                """
                <div class="panel-heading result-heading">
                    <div>
                        <span>Road review</span>
                        <h2>Inspection result</h2>
                    </div>
                </div>
                """
            )

            status_output = gr.HTML(
                status_html("waiting", "Ready for a road photo", "Your result will appear after the image is checked."),
                elem_classes=["status-output"],
            )

            image_output = gr.Image(
                type="pil",
                label="Road damage result",
                show_label=False,
                height="max(250px, calc(100dvh - 700px))",
                buttons=["download", "fullscreen"],
                elem_id="result-image",
            )

            gr.HTML(
                """
                <div class="report-heading">
                    <h2>Detected damage</h2>
                    <span>Results from this photo</span>
                </div>
                """
            )
            detections_output = gr.HTML(empty_report_html())

    detect_button.click(
        fn=analyze_road_image,
        inputs=[image_input],
        outputs=[image_output, status_output, detections_output],
    )


if __name__ == "__main__":
    demo.launch(theme=theme, css=CSS)
