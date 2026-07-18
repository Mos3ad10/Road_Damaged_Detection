from pathlib import Path
import sys

from gradio_deploy.detector import detect_road_damage


APP_DIR = Path(__file__).resolve().parent
SAMPLE_IMAGE = APP_DIR / "test images" / "China_Drone_China_Drone_000095.jpg"


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
        return "Clear match"
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
    <section class="condition-state {tone}" aria-live="polite">
        <span class="condition-indicator" aria-hidden="true"></span>
        <div>
            <p>Road condition</p>
            <h3>{label}</h3>
            <span>{message}</span>
        </div>
    </section>
    """


def empty_report_html() -> str:
    return """
    <section class="findings-empty">
        <div class="empty-mark" aria-hidden="true">
            <i></i><i></i><i></i>
        </div>
        <div>
            <h3>No findings yet</h3>
            <p>Checked areas will appear here.</p>
        </div>
    </section>
    """


def detections_report_html(detections) -> str:
    if not detections:
        return """
        <section class="findings-empty clear">
            <div class="clear-check" aria-hidden="true">&#10003;</div>
            <div>
                <h3>No visible damage</h3>
                <p>No cracks or potholes were found in this photo.</p>
            </div>
        </section>
        """

    cards = []
    for detection in detections[:4]:
        score = detection.confidence * 100
        cards.append(
            f"""
            <article class="finding-row {damage_tone(detection.damage_type)}">
                <span class="finding-swatch" aria-hidden="true"></span>
                <div>
                    <h4>{detection.damage_type}</h4>
                    <p>{certainty_label(detection.confidence)}</p>
                </div>
                <strong>{score:.0f}%</strong>
            </article>
            """
        )

    remaining = len(detections) - len(cards)
    remaining_html = (
        f'<p class="remaining-findings">{remaining} more marked on the photo</p>'
        if remaining > 0
        else ""
    )
    return f"""
    <section class="findings-result">
        <div class="findings-count">
            <strong>{len(detections)}</strong>
            <span>damaged area{'s' if len(detections) != 1 else ''}</span>
        </div>
        <div class="finding-list">{''.join(cards)}</div>
        {remaining_html}
    </section>
    """


def analyze_road_image(image):
    if image is None:
        return (
            None,
            status_html(
                "waiting",
                "Photo needed",
                "Add a road photo before checking its condition.",
            ),
            empty_report_html(),
        )

    try:
        annotated, detections = detect_road_damage(image)
    except Exception:
        return (
            None,
            status_html(
                "error",
                "Photo could not be checked",
                "Choose a clear JPG or PNG road photo and try again.",
            ),
            empty_report_html(),
        )

    if detections:
        count = len(detections)
        status = status_html(
            "damage",
            "Damage found",
            f"{count} damaged area{'s' if count != 1 else ''} marked on the photo.",
        )
    else:
        status = status_html(
            "clear",
            "Road looks clear",
            "No visible cracks or potholes were found.",
        )

    return annotated, status, detections_report_html(detections)


CSS = """
:root {
    --night: #080a0c;
    --asphalt: #0e1114;
    --panel: #13171a;
    --panel-strong: #191e22;
    --line: #30373d;
    --line-soft: #242a2f;
    --text: #f3f5f6;
    --muted: #9aa4ab;
    --yellow: #f4c247;
    --yellow-hover: #ffd568;
    --coral: #f06d50;
    --cyan: #55bac4;
    --violet: #a78bd8;
    --green: #55b98a;
}

html,
body {
    width: 100%;
    height: 100%;
    min-height: 0;
    margin: 0;
    overflow: hidden !important;
    background: var(--night);
}

body {
    overflow: hidden !important;
}

.gradio-container {
    width: 100% !important;
    max-width: none !important;
    height: 100dvh !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
    color: var(--text) !important;
    background: var(--night) !important;
    font-family: "Segoe UI Variable", "Segoe UI", Arial, sans-serif !important;
    letter-spacing: 0 !important;
}

.gradio-container > .main,
.gradio-container .main,
.gradio-container .contain,
.gradio-container main,
.gradio-container main > div:first-child {
    width: 100% !important;
    max-width: none !important;
    height: 100% !important;
    min-height: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    gap: 0 !important;
    overflow: hidden !important;
}

.site-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    height: 68px;
    min-height: 68px;
    padding: 0 30px;
    background: #0b0e10;
    border-bottom: 1px solid var(--line);
}

.brand {
    display: flex;
    align-items: center;
    gap: 13px;
}

.brand-road {
    position: relative;
    width: 34px;
    height: 42px;
    overflow: hidden;
    background: var(--panel-strong);
    border: 1px solid #465058;
    border-radius: 3px;
}

.brand-road::before {
    content: "";
    position: absolute;
    top: -8px;
    bottom: -8px;
    left: 15px;
    width: 3px;
    background: repeating-linear-gradient(
        180deg,
        var(--yellow) 0 9px,
        transparent 9px 16px
    );
}

.brand h1 {
    margin: 0;
    color: var(--text);
    font-family: "Bahnschrift SemiCondensed", "Arial Narrow", sans-serif;
    font-size: 1.35rem;
    font-weight: 720;
    line-height: 1;
    letter-spacing: 0;
}

.brand p {
    margin: 4px 0 0;
    color: var(--muted);
    font-size: 0.75rem;
}

.header-context {
    display: flex;
    align-items: center;
    gap: 9px;
    color: #c4cbd0;
    font-size: 0.82rem;
    font-weight: 650;
}

.header-context::before {
    content: "";
    width: 26px;
    height: 2px;
    background: var(--yellow);
}

.app-page {
    width: 100% !important;
    height: calc(100dvh - 68px) !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 24px 30px 28px !important;
    gap: 20px !important;
    overflow: hidden !important;
    background: var(--night) !important;
}

.app-page > .block.hide-container:first-child {
    flex: 0 0 auto !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
}

.page-intro {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 30px;
    width: 100%;
    padding-bottom: 2px;
}

.page-intro h2 {
    margin: 0;
    color: var(--text);
    font-family: "Bahnschrift SemiCondensed", "Arial Narrow", sans-serif;
    font-size: clamp(1.8rem, 3vw, 2.75rem);
    font-weight: 680;
    line-height: 1;
    letter-spacing: 0;
}

.page-intro p {
    margin: 7px 0 0;
    color: var(--muted);
    font-size: 0.95rem;
}

.damage-spectrum {
    display: grid;
    grid-template-columns: repeat(4, 28px);
    gap: 5px;
    padding-bottom: 6px;
}

.damage-spectrum i {
    display: block;
    height: 4px;
    background: var(--yellow);
}

.damage-spectrum i:nth-child(2) { background: var(--cyan); }
.damage-spectrum i:nth-child(3) { background: var(--violet); }
.damage-spectrum i:nth-child(4) { background: var(--coral); }

.workspace-shell {
    display: grid !important;
    grid-template-columns: minmax(0, 1fr) 370px !important;
    flex: 1 1 0 !important;
    width: 100% !important;
    height: 100% !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    gap: 0 !important;
    overflow: hidden !important;
    background: var(--asphalt) !important;
    border: 1px solid var(--line) !important;
    border-radius: 6px !important;
    box-shadow: 0 22px 60px rgba(0, 0, 0, 0.28) !important;
}

.photo-workspace,
.report-rail {
    width: 100% !important;
    min-width: 0 !important;
    min-height: 0 !important;
    margin: 0 !important;
    border: 0 !important;
    border-radius: 0 !important;
    box-shadow: none !important;
}

.photo-workspace {
    display: flex !important;
    flex-flow: column nowrap !important;
    padding: 20px !important;
    gap: 14px !important;
    background: var(--asphalt) !important;
}

.report-rail {
    display: flex !important;
    flex-flow: column nowrap !important;
    padding: 20px !important;
    gap: 12px !important;
    background: var(--panel) !important;
    border-left: 1px solid var(--line) !important;
}

.section-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    min-height: 28px;
}

.section-heading h3 {
    margin: 0;
    color: var(--text);
    font-size: 0.92rem;
    font-weight: 700;
}

.section-heading span {
    color: var(--muted);
    font-family: Consolas, monospace;
    font-size: 0.7rem;
    text-transform: uppercase;
}

.photo-workspace > .block.hide-container:first-child,
.report-rail > .block.hide-container:first-child,
.report-rail > .block.hide-container:last-child {
    flex: 0 0 auto !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
}

.photo-grid {
    display: grid !important;
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
    flex: 1 1 0 !important;
    width: 100% !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    gap: 12px !important;
}

.photo-pane {
    display: flex !important;
    flex-flow: column nowrap !important;
    width: 100% !important;
    min-width: 0 !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    gap: 9px !important;
    background: transparent !important;
    border: 0 !important;
    border-radius: 0 !important;
    box-shadow: none !important;
}

.pane-label {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 25px;
}

.pane-label strong {
    color: #d9dfe2;
    font-size: 0.8rem;
}

.pane-label span {
    color: var(--muted);
    font-size: 0.7rem;
}

.photo-pane > .block.hide-container:first-child {
    flex: 0 0 25px !important;
    width: 100% !important;
    height: 25px !important;
    min-height: 25px !important;
    margin: 0 !important;
    padding: 0 !important;
}

#source-image,
#result-image {
    flex: 1 1 0 !important;
    width: 100% !important;
    height: 100% !important;
    min-height: 0 !important;
    overflow: hidden !important;
    background: #07090a !important;
    border: 1px solid var(--line) !important;
    border-radius: 4px !important;
    box-shadow: none !important;
}

#source-image:hover {
    border-color: #6c7378 !important;
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
    width: 100% !important;
    height: 100% !important;
    min-height: 0 !important;
    background: #07090a !important;
}

#source-image img,
#result-image img {
    max-width: 100% !important;
    max-height: 100% !important;
    object-fit: contain !important;
}

#source-image button,
#source-image .wrap *,
#result-image .wrap * {
    color: #dce1e3 !important;
}

.report-title h3 {
    font-family: "Bahnschrift SemiCondensed", "Arial Narrow", sans-serif;
    font-size: 1.08rem;
}

#detect-button {
    flex: 0 0 54px !important;
    width: 100% !important;
    min-height: 54px !important;
    margin: 0 !important;
    color: #17191a !important;
    background: var(--yellow) !important;
    border: 1px solid var(--yellow) !important;
    border-radius: 4px !important;
    box-shadow: none !important;
    font-size: 0.98rem !important;
    font-weight: 800 !important;
    transition: background 140ms ease, transform 140ms ease !important;
}

#detect-button:hover {
    color: #111314 !important;
    background: var(--yellow-hover) !important;
    transform: translateY(-1px);
}

.status-output,
.findings-output {
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
    background: transparent !important;
    border: 0 !important;
}

.status-output {
    flex: 0 0 auto !important;
}

.findings-output {
    flex: 1 1 0 !important;
    min-height: 180px !important;
}

.condition-state {
    display: grid;
    grid-template-columns: 12px minmax(0, 1fr);
    align-items: center;
    gap: 13px;
    width: 100%;
    min-height: 116px;
    padding: 17px;
    background: var(--asphalt);
    border: 1px solid var(--line-soft);
    border-left: 3px solid var(--yellow);
    border-radius: 4px;
}

.condition-indicator {
    width: 10px;
    height: 10px;
    background: var(--yellow);
    border-radius: 50%;
    box-shadow: 0 0 0 5px rgba(244, 194, 71, 0.11);
}

.condition-state.damage,
.condition-state.error {
    border-left-color: var(--coral);
}

.condition-state.damage .condition-indicator,
.condition-state.error .condition-indicator {
    background: var(--coral);
    box-shadow: 0 0 0 5px rgba(240, 109, 80, 0.11);
}

.condition-state.clear {
    border-left-color: var(--green);
}

.condition-state.clear .condition-indicator {
    background: var(--green);
    box-shadow: 0 0 0 5px rgba(85, 185, 138, 0.11);
}

.condition-state p,
.condition-state h3,
.condition-state span,
.findings-empty h3,
.findings-empty p,
.finding-row h4,
.finding-row p {
    margin: 0;
}

.condition-state p {
    color: var(--muted);
    font-size: 0.68rem;
    font-weight: 750;
    text-transform: uppercase;
}

.condition-state h3 {
    margin-top: 5px;
    color: var(--text);
    font-size: 1.05rem;
}

.condition-state div > span {
    display: block;
    margin-top: 5px;
    color: var(--muted);
    font-size: 0.82rem;
    line-height: 1.35;
}

.findings-empty,
.findings-result {
    width: 100%;
    height: 100%;
    min-height: 180px;
    padding: 16px;
    overflow: auto;
    background: var(--asphalt);
    border: 1px solid var(--line-soft);
    border-radius: 4px;
}

.findings-empty {
    display: flex;
    align-items: center;
    gap: 14px;
}

.empty-mark {
    display: flex;
    width: 42px;
    height: 50px;
    flex: 0 0 42px;
    align-items: center;
    justify-content: space-evenly;
    background: var(--panel-strong);
    border: 1px solid #3c454b;
    border-radius: 3px;
}

.empty-mark i {
    width: 3px;
    height: 22px;
    background: var(--yellow);
}

.empty-mark i:nth-child(2) { height: 31px; background: var(--cyan); }
.empty-mark i:nth-child(3) { height: 17px; background: var(--coral); }

.findings-empty h3 {
    color: var(--text);
    font-size: 0.96rem;
}

.findings-empty p {
    margin-top: 5px;
    color: var(--muted);
    font-size: 0.8rem;
    line-height: 1.35;
}

.clear-check {
    display: grid;
    width: 38px;
    height: 38px;
    flex: 0 0 38px;
    place-items: center;
    color: #07110c;
    background: var(--green);
    border-radius: 50%;
    font-weight: 900;
}

.findings-result {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.findings-count {
    display: flex;
    align-items: baseline;
    gap: 8px;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--line-soft);
}

.findings-count strong {
    color: var(--yellow);
    font-family: "Bahnschrift SemiCondensed", "Arial Narrow", sans-serif;
    font-size: 1.7rem;
    line-height: 1;
}

.findings-count span {
    color: var(--muted);
    font-size: 0.76rem;
}

.finding-list {
    display: flex;
    flex-direction: column;
    gap: 7px;
}

.finding-row {
    display: grid;
    grid-template-columns: 4px minmax(0, 1fr) auto;
    align-items: center;
    gap: 10px;
    min-height: 54px;
    padding: 8px 10px;
    background: var(--panel);
    border: 1px solid var(--line-soft);
    border-radius: 3px;
}

.finding-swatch {
    width: 4px;
    height: 30px;
    background: var(--yellow);
}

.finding-row.cross .finding-swatch { background: var(--cyan); }
.finding-row.surface .finding-swatch { background: var(--violet); }
.finding-row.pothole .finding-swatch { background: var(--coral); }

.finding-row h4 {
    overflow: hidden;
    color: var(--text);
    font-size: 0.84rem;
    white-space: nowrap;
    text-overflow: ellipsis;
}

.finding-row p {
    margin-top: 3px;
    color: var(--muted);
    font-size: 0.72rem;
}

.finding-row > strong {
    color: #d9dfe2;
    font-size: 0.8rem;
}

.remaining-findings {
    margin: 0;
    color: var(--muted);
    font-size: 0.73rem;
}

.damage-key {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 6px 12px;
    padding-top: 2px;
}

.damage-key span {
    display: flex;
    align-items: center;
    gap: 7px;
    min-width: 0;
    color: var(--muted);
    font-size: 0.69rem;
    white-space: nowrap;
}

.damage-key i {
    width: 13px;
    height: 3px;
    flex: 0 0 13px;
    background: var(--yellow);
}

.damage-key span:nth-child(2) i { background: var(--cyan); }
.damage-key span:nth-child(3) i { background: var(--violet); }
.damage-key span:nth-child(4) i { background: var(--coral); }

.gradio-container button:focus-visible,
.gradio-container input:focus-visible {
    outline: 3px solid rgba(85, 186, 196, 0.48) !important;
    outline-offset: 2px;
}

.gradio-container footer {
    display: none !important;
}

@media (max-width: 1120px) {
    .workspace-shell {
        grid-template-columns: minmax(0, 1fr) 330px !important;
    }
}

@media (max-width: 820px) {
    .site-header {
        height: 58px;
        min-height: 58px;
        padding: 0 16px;
    }

    .header-context {
        display: none;
    }

    .app-page {
        height: calc(100dvh - 58px) !important;
        min-height: 0 !important;
        padding: 12px 16px 14px !important;
        gap: 10px !important;
    }

    .workspace-shell {
        display: grid !important;
        grid-template-columns: minmax(0, 1fr) !important;
        grid-template-rows: minmax(0, 0.82fr) minmax(0, 1.18fr) !important;
        flex: 1 1 0 !important;
        height: 100% !important;
        min-height: 0 !important;
        overflow: hidden !important;
    }

    .photo-workspace,
    .report-rail {
        height: 100% !important;
        min-height: 0 !important;
        padding: 12px !important;
        gap: 8px !important;
    }

    .photo-grid {
        display: grid !important;
        grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        flex: 1 1 0 !important;
        height: 100% !important;
        min-height: 0 !important;
        gap: 8px !important;
    }

    .photo-pane {
        flex: 1 1 0 !important;
        height: 100% !important;
        min-height: 0 !important;
        gap: 6px !important;
    }

    .pane-label span {
        display: none;
    }

    #detect-button {
        display: flex !important;
        flex-basis: 46px !important;
        min-height: 46px !important;
    }

    #source-image,
    #result-image {
        flex: 1 1 0 !important;
        height: 100% !important;
        min-height: 0 !important;
    }

    .report-rail {
        border-top: 1px solid var(--line) !important;
        border-left: 0 !important;
    }

    .condition-state {
        min-height: 78px;
        padding: 10px 12px;
        gap: 10px;
    }

    .condition-state h3 {
        margin-top: 3px;
        font-size: 0.92rem;
    }

    .condition-state div > span {
        margin-top: 3px;
        font-size: 0.72rem;
        line-height: 1.2;
    }

    .findings-output {
        flex: 1 1 0 !important;
        min-height: 0 !important;
    }

    .findings-empty,
    .findings-result {
        min-height: 0;
        padding: 10px 12px;
        overflow: hidden;
    }

    .findings-count {
        padding-bottom: 6px;
    }

    .finding-list {
        gap: 4px;
    }

    .finding-row {
        min-height: 44px;
        padding: 6px 8px;
    }

    .finding-row:nth-child(n+2) {
        display: none;
    }

    .damage-key {
        display: none;
    }
}

@media (max-width: 560px) {
    .brand h1 {
        font-size: 1.12rem;
    }

    .brand p {
        display: none;
    }

    .page-intro h2 {
        font-size: 1.55rem;
    }

    .page-intro p {
        margin-top: 4px;
        font-size: 0.8rem;
    }

    .damage-spectrum {
        display: none;
    }

    .section-heading span,
    .pane-label span {
        font-size: 0.6rem;
    }

    .pane-label strong {
        font-size: 0.72rem;
    }
}

@media (max-height: 780px) {
    .site-header {
        height: 60px;
        min-height: 60px;
    }

    .brand-road {
        width: 30px;
        height: 36px;
    }

    .brand-road::before {
        left: 13px;
    }

    .app-page {
        height: calc(100dvh - 60px) !important;
        padding-top: 14px !important;
        padding-bottom: 16px !important;
        gap: 12px !important;
    }

    .page-intro h2 {
        font-size: 1.8rem;
    }

    .page-intro p {
        margin-top: 4px;
        font-size: 0.82rem;
    }

    .photo-workspace,
    .report-rail {
        padding: 14px !important;
        gap: 8px !important;
    }

    #detect-button {
        flex-basis: 46px !important;
        min-height: 46px !important;
    }

    .condition-state {
        min-height: 88px;
        padding: 11px 13px;
    }

    .findings-output,
    .findings-empty,
    .findings-result {
        min-height: 0 !important;
    }
}

@media (max-width: 820px) and (max-height: 780px) {
    .site-header {
        height: 54px;
        min-height: 54px;
    }

    .app-page {
        height: calc(100dvh - 54px) !important;
        padding: 9px 12px 10px !important;
        gap: 8px !important;
    }

    .page-intro h2 {
        font-size: 1.4rem;
    }

    .page-intro p {
        font-size: 0.75rem;
    }

    .photo-workspace,
    .report-rail {
        padding: 9px !important;
        gap: 6px !important;
    }

    .condition-state {
        min-height: 68px;
        padding: 8px 10px;
    }

    .condition-state div > span {
        display: none;
    }

    .findings-empty,
    .findings-result {
        padding: 8px 10px;
    }
}

@media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
        scroll-behavior: auto !important;
        transition: none !important;
    }
}
"""


theme = gr.themes.Base(
    primary_hue="amber",
    neutral_hue="zinc",
).set(
    body_background_fill="#080a0c",
    block_background_fill="#13171a",
    block_border_color="#30373d",
    button_primary_background_fill="#f4c247",
    button_primary_text_color="#17191a",
    body_text_color="#f3f5f6",
    body_text_color_subdued="#9aa4ab",
)


with gr.Blocks(
    title="Road Damage Detector",
    fill_height=True,
    fill_width=True,
) as demo:
    gr.HTML(
        """
        <header class="site-header">
            <div class="brand">
                <div class="brand-road" aria-hidden="true"></div>
                <div>
                    <h1>Road Damage Detector</h1>
                    <p>Road condition, clearly marked</p>
                </div>
            </div>
            <div class="header-context">Road photo check</div>
        </header>
        """
    )

    with gr.Column(elem_classes=["app-page"]):
        gr.HTML(
            """
            <div class="page-intro">
                <div>
                    <h2>Road condition check</h2>
                    <p>Cracks and potholes, clearly marked.</p>
                </div>
                <div class="damage-spectrum" aria-hidden="true">
                    <i></i><i></i><i></i><i></i>
                </div>
            </div>
            """
        )

        with gr.Row(equal_height=True, elem_classes=["workspace-shell"]):
            with gr.Column(elem_classes=["photo-workspace"]):
                gr.HTML(
                    """
                    <div class="section-heading">
                        <h3>Road photo</h3>
                        <span>Original / checked</span>
                    </div>
                    """
                )
                with gr.Row(equal_height=True, elem_classes=["photo-grid"]):
                    with gr.Column(elem_classes=["photo-pane"]):
                        gr.HTML(
                            """
                            <div class="pane-label">
                                <strong>Original</strong>
                                <span>Add or replace photo</span>
                            </div>
                            """
                        )
                        image_input = gr.Image(
                            value=str(SAMPLE_IMAGE),
                            type="pil",
                            label="Road photo",
                            show_label=False,
                            sources=["upload", "clipboard"],
                            buttons=[],
                            placeholder="Add a road photo",
                            elem_id="source-image",
                        )

                    with gr.Column(elem_classes=["photo-pane"]):
                        gr.HTML(
                            """
                            <div class="pane-label">
                                <strong>Checked photo</strong>
                                <span>Marked damage</span>
                            </div>
                            """
                        )
                        image_output = gr.Image(
                            type="pil",
                            label="Checked road photo",
                            show_label=False,
                            buttons=["download", "fullscreen"],
                            elem_id="result-image",
                        )

            with gr.Column(elem_classes=["report-rail"]):
                gr.HTML(
                    """
                    <div class="section-heading report-title">
                        <h3>Condition report</h3>
                        <span>Current photo</span>
                    </div>
                    """
                )
                detect_button = gr.Button(
                    "Check this photo",
                    variant="primary",
                    elem_id="detect-button",
                )
                status_output = gr.HTML(
                    status_html(
                        "waiting",
                        "Ready to check",
                        "Use the sample road or add your own photo.",
                    ),
                    elem_classes=["status-output"],
                )
                detections_output = gr.HTML(
                    empty_report_html(),
                    elem_classes=["findings-output"],
                )
                gr.HTML(
                    """
                    <div class="damage-key" aria-label="Road damage types">
                        <span><i></i>Long crack</span>
                        <span><i></i>Cross crack</span>
                        <span><i></i>Surface crack</span>
                        <span><i></i>Pothole</span>
                    </div>
                    """
                )

    detect_button.click(
        fn=analyze_road_image,
        inputs=[image_input],
        outputs=[image_output, status_output, detections_output],
    )
if __name__ == "__main__":
    demo.launch(theme=theme, css=CSS, server_port=7861)
