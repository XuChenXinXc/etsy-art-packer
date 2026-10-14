# EtsyArtPacker (Etsy 5-in-1 Wall Art Resizer & 300 DPI Packager)

> **专为欧美 Etsy 卖家与按需印刷（Print-on-Demand / POD）创作者打造的 100% 免费轻量生产力工具。**  
> 纯前端运行（Client-Side Only），无限制、无水印、保护隐私。通过精准 Google 搜索流量与 **Google AdSense 广告** 实现纯被动美金收益。

---

## 一、 为什么选择“纯免费 + Google 广告”变现模型？

1. **零交易摩擦，用户规模扩大 10 倍**：
   - 竞品（如 SnapToSize）强制收取 $14.99/月的高昂订阅费，且免费版强制加水印，导致大量中小卖家反感；
   - 本工具打出 **“100% Free · No Watermark · 100% Private”** 旗号，在 Reddit、Facebook 群组和 YouTube 评论区具备极其恐怖的口碑自发传播力。
2. **欧美高价值广告回报（高 eCPM）**：
   - 访客全是在线做生意的小卖家，属于极高商业价值的人群；
   - 欧美设计、印刷、独立站电商相关广告在 Google AdSense 的千次展示收益（RPM）通常在 **$8 ~ $20 美元**；
   - 随着 SEO 排名稳定，每月仅需几万次访问，即可持续贡献 **$200 ~ $600 美元（约 1,500 ~ 4,500 元人民币）** 的纯被动广告收益。
3. **中国开发者合规无障碍**：
   - 彻底免去注册海外公司、Stripe 审核等繁琐麻烦；
   - Google AdSense 官方直接支持中国大陆居民身份证注册，广告收益直接电汇到国内储蓄卡。

---

## 二、 核心作用与解决痛点

在欧美电商平台（Etsy、Shopify、Printify、Redbubble），买家购买数码壁画后需要自行打印装框：
- 宜家相框是 **4:5 比例**（8x10", 16x20"）
- 画廊海报是 **2:3 比例**（12x18", 24x36"）
- 标准相框是 **3:4 比例**（18x24"）
- 欧洲/澳洲买家需要 **ISO 标准**（A1~A5）
- 经典肖像框是 **11:14 比例**

卖家上传 1 款新品，必须在 Photoshop 里手动算尺寸、裁切 5 次、注入 300 DPI 并打包成 Zip。**本工具让卖家拖入原图，1 秒自动���成包含这 5 大主流比例及买家相框指南的交付 ZIP 包。**

---

## 三、 网页内广告位布局规划

网页中已经预留好两个高点击率、不打扰用户体验的标准广告位：
1. **工作区广告位（Top Responsive Ad）**：位于上传后 5 大切片卡片下方、生成按钮上方（用户等待切片完成时的黄金视线聚焦区）；
2. **底部通栏广告位（Bottom Banner Ad）**：位于核心价值特性说明上方。

---

## 四、 Google AdSense 申请与上线流程

1. **独立域名绑定**：
   - 在 Cloudflare 或 Porkbun 购买一个域名（例如 `etsyartpacker.com`，约 60-80 元/年）；
   - 在 Vercel 后台点击 **Settings -> Domains** 添加绑定；
   - *(注意：Google AdSense 要求申请网站必须拥有自定义一级域名，不能直接用 `.vercel.app` 免费二级域名申请)*。
2. **注册 AdSense 账号**：
   - 打开 [google.com/adsense](https://www.google.com/adsense)，使用你的 Google 账号登录；
   - 填写你的网站地址（你的独立域名），收款人姓名与地址填写身份证真实信息；
3. **复制代码至网页**：
   - Google 会提供一段自动广告代码（类似 `<script async src="https://pagead2.googlesyndication.com/..."></script>`）；
   - 将该代码直接粘贴进 `index.html` 的 `<head>` 区域，推送到 GitHub 即可自动生效！
