import functools
import random
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright


@pytest.fixture(scope="session")
def base_url():
    project_dir = Path(__file__).resolve().parents[1]
    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(project_dir))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture
def app_page(browser, base_url):
    page = browser.new_page(viewport={"width": 1280, "height": 900})

    # 只放行本地站点资源：测试不依赖外网，也不会带真实发布商 ID 请求广告、字体和统计服务。
    def block_external(route):
        if route.request.url.startswith(base_url):
            route.continue_()
        else:
            route.abort()

    page.route("**/*", block_external)
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(base_url, wait_until="load")
    try:
        yield page
    finally:
        page.close()
    assert errors == [], f"页面出现未捕获的脚本错误：{errors}"


@pytest.fixture(scope="session")
def test_images(tmp_path_factory):
    image_dir = tmp_path_factory.mktemp("artwork")
    images = {
        "normal": ((800, 1200), "#ff2020"),
        "replacement": ((1200, 800), "#2040ff"),
        "cap": ((7200, 10800), "#ff2020"),
        "cap_landscape": ((10800, 7200), "#ff2020"),
        "narrow": ((1200, 4800), "#ff2020"),
        # 预检卡片会同时出现 Flawless / Good / Low 三档徽章
        "tiers": ((3000, 4500), "#c04080"),
    }
    for name, (size, color) in images.items():
        with Image.new("RGB", size, color) as image:
            image.save(image_dir / f"{name}.png")
    # 底色上叠加一个色块：(尺寸, 底色, 色块区域, 色块颜色)
    block_images = {
        "edge": ((1600, 400), "white", (20, 20, 1579, 379), "#2040ff"),
        # 右下角模拟签名，验证留白取色不会被单个角落带偏
        "signature": ((1600, 400), "white", (1540, 370, 1599, 399), "black"),
        "halves_landscape": ((1600, 400), "#ff0000", (800, 0, 1599, 399), "#0000ff"),
        "halves_portrait": ((400, 1600), "#ff0000", (0, 800, 399, 1599), "#0000ff"),
    }
    for name, (size, color, box, fill) in block_images.items():
        with Image.new("RGB", size, color) as image:
            ImageDraw.Draw(image).rectangle(box, fill=fill)
            image.save(image_dir / f"{name}.png")
    with Image.new("RGB", (100, 100), "#ff2020") as image:
        image.save(image_dir / "artwork.gif")
    (image_dir / "oversized.png").write_bytes(bytes(51 * 1024 * 1024))
    (image_dir / "corrupt.png").write_bytes(b"not a valid PNG")
    yield image_dir
    for image_path in image_dir.iterdir():
        image_path.unlink()
    image_dir.rmdir()


@pytest.fixture(scope="session")
def noise_image(tmp_path_factory):
    image_path = tmp_path_factory.mktemp("noise") / "noise.jpg"
    # 使用固定随机种子生成高细节图片，验证真实编码后的文件大小。
    pixels = random.Random(20261016).randbytes(4800 * 7200 * 3)
    with Image.frombytes("RGB", (4800, 7200), pixels) as image:
        image.save(image_path, quality=95, subsampling=2)
    del pixels
    assert image_path.stat().st_size < 50 * 1024 * 1024
    yield image_path
    image_path.unlink()
    image_path.parent.rmdir()
