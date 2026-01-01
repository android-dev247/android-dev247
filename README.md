<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>android-dev247 - 安卓搞机开发者</title>
    <style>
        /* 全局样式，贴合GitHub浅色主题 */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }
        body {
            background-color: #f6f8fa;
            color: #24292e;
            line-height: 1.5;
            padding: 20px;
            max-width: 900px;
            margin: 0 auto;
        }
        /* 头部信息卡片 */
        .profile-header {
            background-color: #ffffff;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            padding: 24px;
            margin-bottom: 20px;
        }
        .profile-username {
            font-size: 24px;
            font-weight: 600;
            color: #0366d6;
            margin-bottom: 8px;
        }
        .profile-bio {
            font-size: 16px;
            color: #586069;
            margin-bottom: 16px;
        }
        .profile-status {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
            color: #24292e;
        }
        /* 核心信息卡片 */
        .profile-content {
            background-color: #ffffff;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            padding: 24px;
        }
        .content-title {
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .content-list {
            list-style: none;
            margin-left: 20px;
        }
        .content-list li {
            margin-bottom: 12px;
            font-size: 16px;
            display: flex;
            align-items: flex-start;
            gap: 8px;
        }
        .content-list li span.icon {
            color: #959da5;
            margin-top: 4px;
        }
        .content-list li a {
            color: #0366d6;
            text-decoration: none;
        }
        .content-list li a:hover {
            text-decoration: underline;
        }
        /* 响应式适配 */
        @media (max-width: 768px) {
            body {
                padding: 10px;
            }
            .profile-header, .profile-content {
                padding: 16px;
            }
            .profile-username {
                font-size: 20px;
            }
            .content-title {
                font-size: 18px;
            }
        }
    </style>
</head>
<body>
    <!-- 个人信息头部 -->
    <div class="profile-header">
        <div class="profile-username">android-dev247</div>
        <div class="profile-bio">专注Zygisk/KernelSU模块开发，适配红米K50/澎湃OS</div>
        <div class="profile-status">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M8 1.5a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13zM0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8z" fill="#24292e"/>
                <path d="M8 4.25a.75.75 0 0 1 .75.75v3.5a.75.75 0 0 1-1.5 0V5a.75.75 0 0 1 .75-.75zm0 8a1 1 0 1 1 0-2 1 1 0 0 1 0 2z" fill="#24292e"/>
            </svg>
            活跃于GitHub · 安卓搞机领域
        </div>
    </div>

    <!-- 核心信息内容 -->
    <div class="profile-content">
        <h2 class="content-title">
            <span>👋 Hi there!</span>
        </h2>
        <ul class="content-list">
            <li>
                <span class="icon">🔭</span>
                <span>I’m currently working on <strong>Zygisk模块开发与KernelSU适配</strong>，主攻红米K50澎湃OS系统的模块注入优化</span>
            </li>
            <li>
                <span class="icon">🌱</span>
                <span>I’m currently learning <strong>安卓底层源码修改、Magisk/Zygisk核心注入原理</strong></span>
            </li>
            <li>
                <span class="icon">👯</span>
                <span>I’m looking to collaborate on <strong>澎湃OS兼容的LSPosed模块开发、Root隐藏方案优化</strong></span>
            </li>
            <li>
                <span class="icon">🤔</span>
                <span>I’m looking for help with <strong>红米K50内核调试、Zygisk Next高版本适配问题</strong></span>
            </li>
            <li>
                <span class="icon">💬</span>
                <span>Ask me about <strong>Android Root、Zygisk模块注入、KernelSU使用与调试</strong></span>
            </li>
            <li>
                <span class="icon">📫</span>
                <span>How to reach me: <a href="mailto:2470018839@qq.com">2470018839@qq.com</a></span>
            </li>
            <li>
                <span class="icon">⚡</span>
                <span>Fun fact: <strong>用Zygisk给澎湃OS注入过10+款功能模块，零系统崩溃记录</strong></span>
            </li>
        </ul>
    </div>
</body>
</html>
