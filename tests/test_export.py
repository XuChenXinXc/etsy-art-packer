import re
import shutil
from io import BytesIO
from zipfile import ZipFile

import pytest
from PIL import Image
from playwright.sync_api import expect

# 与页面保持一致：Etsy 单文件上限按十进制 20MB 计算。
ETSY_MAX_FILE_BYTES = 20 * 1000 * 1000
CONTROL_SELECTORS = (
    "#btn-process",
    "#btn-reset",
    "#file-input",
    "#crop-strategy",
    "#mobile-sticky-btn",
)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# 导出失败场景：注入的故障脚本，以及状态栏应展示的错误信息。
EXPORT_FAILURES = [
    pytest.param(
        """() => {
          HTMLCanvasElement.prototype.toBlob = function(callback) {
            queueMicrotask(() => callback(null));
          };
        }""",
        "Failed to encode image",
        id="encode",
    ),
    pytest.param(
        """() => {
          Blob.prototype.arrayBuffer = () => Promise.reject(new Error('JPEG read failed'));
        }""",
        "JPEG read failed",
        id="read-jpeg",
    ),
    pytest.param(
        # 模拟 iOS Safari：画布超过面积上限时不抛异常，只返回空白画布。
        """() => {
          const original = CanvasRenderingContext2D.prototype.getImageData;
          CanvasRenderingContext2D.prototype.getImageData = function(...args) {
            const { width, height } = this.canvas;
            if (width * height > 1000000) return new ImageData(1, 1);
            return original.apply(this, args);
          };
        }""",
        "cannot create a 900 × 1200 px image",
        id="canvas-limit",
    ),
    pytest.param(
        # 模拟 Safari 画布总内存超限：大画布拿不到 2D 上下文。
        """() => {
          const original = HTMLCanvasElement.prototype.getContext;
          HTMLCanvasElement.prototype.getContext = function(...args) {
            if (this.width * this.height > 1000000) return null;
            return original.apply(this, args);
          };
        }""",
        "cannot create a 900 × 1200 px image",
        id="no-context",
    ),
]

# 不是 Tailwind 工具类、本来就没有样式规则的 class。
CLASSES_WITHOUT_RULES = {"prose", "prose-invert", "ratio-card"}
# 返回当前 DOM 里在所有样式表规则中都找不到的 class。
MISSING_CSS_RULES = r"""() => {
  const ruleClasses = new Set();
  const walk = rules => {
    for (const rule of rules) {
      const selector = rule.selectorText || '';
      for (const match of selector.matchAll(/\.((?:\\[0-9a-f]{1,6} ?|\\.|[\w-])+)/gi)) {
        ruleClasses.add(match[1]);
      }
      if (rule.cssRules) walk(rule.cssRules);
    }
  };
  for (const sheet of document.styleSheets) walk(sheet.cssRules);
  const classes = new Set();
  document.querySelectorAll('[class]').forEach(el => el.classList.forEach(c => classes.add(c)));
  return [...classes].filter(c => !ruleClasses.has(CSS.escape(c)));
}"""


def load_image(page, image_path):
    page.locator("#file-input").set_input_files(image_path)
    expect(page.locator("#src-name")).to_have_text(image_path.name)


def download_pack(page, destination):
    with page.expect_download() as download_info:
        page.locator("#btn-process").click()
    download_info.value.save_as(destination)
    expect(page.locator("#btn-process")).to_be_enabled()
    return download_info.value


def preview_pixel(page, x, y):
    """读取 2:3 预览画布在相对坐标 (x, y) 处的 RGB。"""
    pixel = page.evaluate(
        """([x, y]) => {
          const canvas = document.getElementById('preview-canvas-2-3');
          const left = Math.floor(canvas.width * x);
          const top = Math.floor(canvas.height * y);
          return Array.from(canvas.getContext('2d').getImageData(left, top, 1, 1).data);
        }""",
        [x, y],
    )
    return tuple(pixel[:3])


def export_pixel(archive, name, x, y):
    """读取导出 JPEG 在相对坐标 (x, y) 处的 RGB。"""
    with Image.open(BytesIO(archive.read(name))) as image:
        return image.getpixel((int(image.width * x), int(image.height * y)))


def missing_css_rules(page):
    """返回当前页面里没有对应 CSS 规则的 class。"""
    return set(page.evaluate(MISSING_CSS_RULES)) - CLASSES_WITHOUT_RULES


@pytest.mark.parametrize(
    ("name", "expected_size"),
    [("cap", (4800, 7200)), ("cap_landscape", (7200, 4800))],
)
def test_large_export_quality_matches_output(
    app_page, test_images, tmp_path, name, expected_size
):
    load_image(app_page, test_images / f"{name}.png")
    expect(app_page.locator("#preflight-grid > div").nth(3)).to_contain_text("200 PPI")
    pack = tmp_path / "cap.zip"
    download_pack(app_page, pack)
    with ZipFile(pack) as archive:
        assert len(archive.namelist()) == 6
        with Image.open(BytesIO(archive.read(f"{name}_Ratio_2x3_300DPI.jpg"))) as image:
            assert image.size == expected_size
            assert image.info["dpi"] == (300, 300)
        guide = archive.read("Printing_Size_Guide.txt").decode()
        assert '24x36": (200 PPI - Standard Print Quality)' in guide
        assert "A1: (212 PPI - Standard Print Quality)" in guide
    pack.unlink()


def test_margin_strategy_updates_quality_and_guide(app_page, test_images, tmp_path):
    load_image(app_page, test_images / "narrow.png")
    card = app_page.locator("#preflight-grid > div").nth(2)
    expect(card).to_contain_text("75 PPI")
    for strategy in ("fit-white", "fit-black", "fit-edge"):
        app_page.get_by_label("Crop Strategy:").select_option(strategy)
        expect(card).to_contain_text("200 PPI")
    pack = tmp_path / "margin.zip"
    download_pack(app_page, pack)
    with ZipFile(pack) as archive:
        with Image.open(BytesIO(archive.read("narrow_Ratio_2x3_300DPI.jpg"))) as image:
            assert image.size == (3200, 4800)
        guide = archive.read("Printing_Size_Guide.txt").decode()
        assert '16x24": (200 PPI - Standard Print Quality)' in guide
    app_page.get_by_label("Crop Strategy:").select_option("center")
    expect(card).to_contain_text("75 PPI")
    pack.unlink()


def test_export_blocks_source_changes_and_keeps_one_artwork(
    app_page, test_images, tmp_path
):
    load_image(app_page, test_images / "normal.png")
    # 暂停首张图片的编码回调，稳定覆盖用户在异步导出间隙操作的场景。
    app_page.evaluate("""() => {
      const original = HTMLCanvasElement.prototype.toBlob;
      HTMLCanvasElement.prototype.toBlob = function(callback, ...args) {
        original.call(this, blob => {
          if (!window.heldEncoding) {
            window.heldEncoding = true;
            window.releaseEncoding = () => callback(blob);
          } else callback(blob);
        }, ...args);
      };
    }""")
    with app_page.expect_download() as download_info:
        app_page.locator("#btn-process").click()
        app_page.wait_for_function("window.heldEncoding === true")
        for selector in CONTROL_SELECTORS:
            expect(app_page.locator(selector)).to_be_disabled()
        app_page.evaluate("""() => {
          const transfer = new DataTransfer();
          transfer.items.add(new File(['invalid'], 'replacement.png', {type:'image/png'}));
          document.getElementById('drop-zone').dispatchEvent(new DragEvent('drop', {
            dataTransfer: transfer, bubbles: true, cancelable: true
          }));
          document.getElementById('btn-reset').dispatchEvent(new MouseEvent('click'));
          document.getElementById('btn-process').dispatchEvent(new MouseEvent('click'));
          window.releaseEncoding();
        }""")
    pack = tmp_path / "one-artwork.zip"
    download_info.value.save_as(pack)
    assert download_info.value.suggested_filename == "normal_Etsy_Print_Pack.zip"
    with ZipFile(pack) as archive:
        jpg_names = [name for name in archive.namelist() if name.endswith(".jpg")]
        assert len(jpg_names) == 5
        for name in jpg_names:
            assert name.startswith("normal_")
            with Image.open(BytesIO(archive.read(name))) as image:
                red, green, blue = image.getpixel((image.width // 2, image.height // 2))
                assert red > 240
                assert green < 50
                assert blue < 50
    expect(app_page.locator("#src-name")).to_have_text("normal.png")
    expect(app_page.locator("#btn-reset")).to_be_enabled()
    pack.unlink()


def test_corrupt_upload_shows_error_and_clears_previous_artwork(app_page, test_images):
    load_image(app_page, test_images / "normal.png")
    app_page.locator("#file-input").set_input_files(test_images / "corrupt.png")
    expect(app_page.locator("#upload-status")).to_be_visible()
    expect(app_page.locator("#upload-status")).to_contain_text(
        "Unable to read or decode this image"
    )
    expect(app_page.locator("#workspace")).to_be_hidden()
    expect(app_page.locator("#btn-process")).to_be_disabled()
    assert app_page.evaluate("sourceImage") is None
    load_image(app_page, test_images / "replacement.png")
    expect(app_page.locator("#upload-status")).to_be_hidden()
    expect(app_page.locator("#btn-process")).to_be_enabled()


@pytest.mark.parametrize(
    ("file_name", "message"),
    [("oversized.png", "exceeds the 50MB limit"), ("artwork.gif", "not supported")],
)
def test_invalid_selection_keeps_current_artwork(
    app_page, test_images, file_name, message
):
    load_image(app_page, test_images / "normal.png")
    app_page.locator("#file-input").set_input_files(test_images / file_name)
    expect(app_page.locator("#upload-status")).to_contain_text(message)
    expect(app_page.locator("#workspace")).to_be_visible()
    expect(app_page.locator("#src-name")).to_have_text("normal.png")
    expect(app_page.locator("#btn-process")).to_be_enabled()


def test_file_read_failure_shows_error_and_disables_export(app_page, test_images):
    # 模拟文件读不到：交给图片的 object URL 已经失效。
    app_page.evaluate("""() => {
      const original = URL.createObjectURL;
      URL.createObjectURL = blob => {
        const url = original(blob);
        URL.revokeObjectURL(url);
        return url;
      };
    }""")
    app_page.locator("#file-input").set_input_files(test_images / "normal.png")
    expect(app_page.locator("#upload-status")).to_be_visible()
    expect(app_page.locator("#upload-status")).to_contain_text(
        "Unable to read or decode this image"
    )
    expect(app_page.locator("#btn-process")).to_be_disabled()


def test_late_file_callback_does_not_replace_newer_upload(app_page, test_images):
    # 拦住第一张图片的 load 事件，等第二张加载完成后再放行。
    app_page.evaluate("""() => {
      const OriginalImage = window.Image;
      let held = false;
      window.Image = class extends OriginalImage {
        constructor(...args) {
          super(...args);
          if (held) return;
          held = true;
          this.addEventListener('load', event => {
            event.stopImmediatePropagation();
            window.releaseEarlierLoad = () => this.onload(event);
          });
        }
      };
    }""")
    app_page.locator("#file-input").set_input_files(test_images / "normal.png")
    app_page.wait_for_function("typeof window.releaseEarlierLoad === 'function'")
    expect(app_page.locator("#btn-process")).to_be_disabled()
    load_image(app_page, test_images / "replacement.png")
    app_page.evaluate("window.releaseEarlierLoad()")
    expect(app_page.locator("#src-name")).to_have_text("replacement.png")
    assert app_page.evaluate("sourceImage.width") == 1200


@pytest.mark.parametrize(("failure_script", "message"), EXPORT_FAILURES)
def test_export_failure_shows_error_and_restores_controls(
    app_page, test_images, failure_script, message
):
    load_image(app_page, test_images / "normal.png")
    app_page.evaluate(failure_script)
    app_page.locator("#btn-process").click()
    expect(app_page.locator("#status-text")).to_contain_text(message)
    for selector in CONTROL_SELECTORS:
        expect(app_page.locator(selector)).to_be_enabled()


def test_canvas_readback_noise_exports_all_files(app_page, test_images, tmp_path):
    load_image(app_page, test_images / "normal.png")
    # 模拟 Safari 指纹防护：1x1 读回时不透明像素的 alpha 被减 2，透明像素保持 0。
    app_page.evaluate("""() => {
      const original = CanvasRenderingContext2D.prototype.getImageData;
      CanvasRenderingContext2D.prototype.getImageData = function(...args) {
        const result = original.apply(this, args);
        if (result.width === 1 && result.height === 1 && result.data[3] > 0) {
          result.data[3] -= 2;
        }
        return result;
      };
    }""")
    pack = tmp_path / "noise.zip"
    download_pack(app_page, pack)
    with ZipFile(pack) as archive:
        assert len(archive.namelist()) == 6
    pack.unlink()


@pytest.mark.parametrize(
    ("image_name", "min_channel"),
    # signature 右下角有深色签名：只取四角像素时留白约为 191 的灰色。
    [("edge", 255), ("signature", 240)],
)
def test_adaptive_margin_matches_image_edges(
    app_page, test_images, tmp_path, image_name, min_channel
):
    load_image(app_page, test_images / f"{image_name}.png")
    app_page.get_by_label("Crop Strategy:").select_option("fit-edge")
    assert min(preview_pixel(app_page, 0.5, 0)) >= min_channel
    pack = tmp_path / "edge.zip"
    download_pack(app_page, pack)
    with ZipFile(pack) as archive:
        pixel = export_pixel(archive, f"{image_name}_Ratio_2x3_300DPI.jpg", 0.5, 0)
    assert min(pixel) >= min_channel
    pack.unlink()


@pytest.mark.parametrize(
    ("image_name", "strategy", "expected"),
    [
        ("halves_landscape", "left", RED),
        ("halves_landscape", "right", BLUE),
        ("halves_portrait", "top", RED),
        ("halves_portrait", "bottom", BLUE),
    ],
)
def test_crop_anchor_keeps_selected_side(
    app_page, test_images, tmp_path, image_name, strategy, expected
):
    load_image(app_page, test_images / f"{image_name}.png")
    app_page.get_by_label("Crop Strategy:").select_option(strategy)
    assert preview_pixel(app_page, 0.5, 0.5) == expected
    pack = tmp_path / "anchor.zip"
    download_pack(app_page, pack)
    with ZipFile(pack) as archive:
        pixel = export_pixel(archive, f"{image_name}_Ratio_2x3_300DPI.jpg", 0.5, 0.5)
    assert all(abs(actual - target) <= 16 for actual, target in zip(pixel, expected))
    pack.unlink()


@pytest.mark.parametrize(
    ("file_name", "base_name"),
    [
        pytest.param("日落.png", "artwork", id="non-ascii"),
        pytest.param("My Art (final).png", "My_Art_final", id="punctuation"),
        pytest.param(f"{'a' * 44} b.png", "a" * 44, id="truncated"),
    ],
)
def test_export_file_names_are_sanitized(
    app_page, test_images, tmp_path, file_name, base_name
):
    image_path = tmp_path / file_name
    shutil.copyfile(test_images / "normal.png", image_path)
    load_image(app_page, image_path)
    pack = tmp_path / "named.zip"
    download = download_pack(app_page, pack)
    assert download.suggested_filename == f"{base_name}_Etsy_Print_Pack.zip"
    with ZipFile(pack) as archive:
        assert f"{base_name}_Ratio_2x3_300DPI.jpg" in archive.namelist()
    pack.unlink()
    image_path.unlink()


@pytest.mark.parametrize("key", ["Enter", "Space"])
def test_keyboard_opens_file_picker_from_upload_zone(app_page, test_images, key):
    upload_zone = app_page.get_by_role(
        "button", name=re.compile("Drag & drop your master artwork")
    )
    for _ in range(10):
        app_page.keyboard.press("Tab")
        if app_page.evaluate("document.activeElement.id") == "drop-zone":
            break
    expect(upload_zone).to_be_focused()
    with app_page.expect_file_chooser() as chooser_info:
        app_page.keyboard.press(key)
    chooser_info.value.set_files(test_images / "normal.png")
    expect(app_page.locator("#src-name")).to_have_text("normal.png")


def test_file_drop_outside_upload_zone_is_blocked(app_page):
    result = app_page.evaluate("""() => {
      const transfer = new DataTransfer();
      transfer.items.add(new File(['x'], 'art.png', {type: 'image/png'}));
      transfer.dropEffect = 'copy';
      const footer = document.querySelector('footer');
      const dragover = new DragEvent('dragover', {
        dataTransfer: transfer, bubbles: true, cancelable: true
      });
      footer.dispatchEvent(dragover);
      const dropEffect = transfer.dropEffect;
      const drop = new DragEvent('drop', {
        dataTransfer: transfer, bubbles: true, cancelable: true
      });
      footer.dispatchEvent(drop);
      return [dragover.defaultPrevented, dropEffect, drop.defaultPrevented];
    }""")
    assert result == [True, "none", True]
    expect(app_page.locator("#workspace")).to_be_hidden()


def test_detailed_export_keeps_each_jpeg_within_etsy_limit(
    app_page, noise_image, tmp_path
):
    load_image(app_page, noise_image)
    pack = tmp_path / "detailed.zip"
    download_pack(app_page, pack)
    assert pack.stat().st_size > ETSY_MAX_FILE_BYTES
    with ZipFile(pack) as archive:
        images = [
            entry for entry in archive.infolist() if entry.filename.endswith(".jpg")
        ]
        assert len(images) == 5
        for entry in images:
            assert entry.file_size <= ETSY_MAX_FILE_BYTES, entry.filename
            with Image.open(BytesIO(archive.read(entry.filename))) as image:
                assert image.info["dpi"] == (300, 300)
    expect(app_page.locator("#status-text")).to_contain_text(
        "Unzip and upload the 5 JPGs individually"
    )
    expect(app_page.locator("#status-text")).to_contain_text(
        "paste the text of Printing_Size_Guide.txt"
    )
    pack.unlink()


@pytest.mark.parametrize("width", [320, 375, 768, 1024])
def test_crop_controls_fit_viewport(app_page, test_images, width):
    app_page.set_viewport_size({"width": width, "height": 812})
    load_image(app_page, test_images / "normal.png")
    for locator in (
        app_page.get_by_text("Crop Strategy:", exact=True),
        app_page.get_by_label("Crop Strategy:"),
    ):
        box = locator.bounding_box()
        assert box["x"] >= 0
        assert box["x"] + box["width"] <= width
    assert app_page.evaluate("document.documentElement.scrollWidth") <= width


@pytest.mark.parametrize("path", ["/privacy/", "/terms/"])
def test_policy_page_classes_have_css_rules(app_page, base_url, path):
    app_page.goto(base_url + path, wait_until="load")
    assert missing_css_rules(app_page) == set()


def test_app_state_classes_have_css_rules(app_page, test_images):
    missing = missing_css_rules(app_page)
    app_page.evaluate("""() => document.getElementById('drop-zone').dispatchEvent(
      new DragEvent('dragover', {dataTransfer: new DataTransfer(), bubbles: true, cancelable: true})
    )""")
    missing |= missing_css_rules(app_page)
    load_image(app_page, test_images / "tiers.png")
    expect(app_page.locator("#preflight-grid > div")).to_contain_text(
        ["Flawless", "Good", "Low"]
    )
    missing |= missing_css_rules(app_page)
    # 直接切到处理中状态，覆盖 updateControls() 切换的 class。
    app_page.evaluate("() => { isProcessing = true; updateControls(); }")
    missing |= missing_css_rules(app_page)
    assert missing == set()
