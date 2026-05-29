/**
 * 天爱验证码 Django 版演示平台 - 前端脚本
 *
 * 使用本地构建的 tianai-captcha-web-sdk，直接通过 window.TAC 初始化。
 * 不使用 CDN 的 load.min.js，避免 track data 被加密编码。
 */

// 验证码配置
const captchaConfig = {
    currentType: "RANDOM",
    baseUrls: {
        genRandom: "/api/captcha/generate",
        genByType: "/api/captcha/generate?type=",
        validate: "/api/captcha/check"
    },
    windowStyles: [
        {
            btnUrl: "https://minio.tianai.cloud/public/captcha-btn/btn3.png",
            bgUrl: "https://minio.tianai.cloud/public/captcha-btn/btn3-bg.jpg",
            logoUrl: null,
            moveTrackMaskBgColor: "#f7b645",
            moveTrackMaskBorderColor: "#ef9c0d"
        },
        {
            btnUrl: "https://minio.tianai.cloud/public/captcha-btn/btn2.png",
            bgUrl: "https://minio.tianai.cloud/public/captcha-btn/btn2-bg.jpg",
            logoUrl: null,
            moveTrackMaskBgColor: "#89d2ff",
            moveTrackMaskBorderColor: "#32a9ff"
        },
        {
            btnUrl: "https://minio.tianai.cloud/public/captcha-btn/btn4.png",
            bgUrl: "https://minio.tianai.cloud/public/captcha-btn/btn4-bg.jpg",
            logoUrl: null,
            moveTrackMaskBgColor: "#cbd3d0",
            moveTrackMaskBorderColor: "#b6bdba"
        }
    ]
};

// 统计数据
const stats = {
    total: 0,
    success: 0,
    fail: 0
};

// 验证码实例
let captchaInstance = null;
let isLoadingCaptcha = false;

$(document).ready(function () {
    // 验证码类型切换事件
    $('.captcha-type').on('click', function () {
        const captchaType = $(this).data('captcha-type');

        if (captchaType) {
            // 更新选中状态
            $('.captcha-type').removeClass('captcha-type-active');
            $(this).addClass('captcha-type-active');

            // 更新表单标题
            const typeText = $(this).text().trim();
            $('#form-title').text('验证码体验(' + typeText + ')');

            // 更新当前类型
            captchaConfig.currentType = captchaType;

            // 销毁现有验证码实例
            if (captchaInstance) {
                captchaInstance.destroyWindow();
                captchaInstance = null;
            }

            // 隐藏结果消息
            $('#result-message').hide();
        }
    });

    // 验证按钮点击
    $('#login-btn').on('click', function () {
        loadCaptcha();
    });
});

/**
 * 加载验证码
 */
function loadCaptcha() {
    // 防抖：如果正在加载，忽略重复点击
    if (isLoadingCaptcha) return;
    isLoadingCaptcha = true;

    let genCaptchaUrl = captchaConfig.baseUrls.genRandom;
    let windowStyle;

    if (captchaConfig.currentType !== "RANDOM") {
        genCaptchaUrl = captchaConfig.baseUrls.genByType + captchaConfig.currentType;
        // 随机选择样式
        windowStyle = captchaConfig.windowStyles[Math.floor(Math.random() * captchaConfig.windowStyles.length)];
    } else {
        windowStyle = captchaConfig.windowStyles[0];
    }

    // 隐藏结果消息
    $('#result-message').hide();

    // 销毁现有验证码实例
    if (captchaInstance) {
        captchaInstance.destroyWindow();
        captchaInstance = null;
    }

    // 使用本地构建的 TAC SDK 直接初始化
    try {
        var config = {
            requestCaptchaDataUrl: genCaptchaUrl,
            validCaptchaUrl: captchaConfig.baseUrls.validate,
            bindEl: "#captcha-div",
            validSuccess: handleCaptchaSuccess,
            validFail: handleCaptchaFail,
            btnRefreshFun: function (el, tac) {
                tac.reloadCaptcha();
            },
            btnCloseFun: function (el, tac) {
                tac.destroyWindow();
                captchaInstance = null;
            }
        };

        var tac = new window.TAC(config, windowStyle);
        captchaInstance = tac.init();
    } catch (error) {
        console.error("验证码加载失败:", error);
        showNotification("验证码加载失败，请重试", "error");
    } finally {
        isLoadingCaptcha = false;
    }
}

/**
 * 验证成功回调
 */
function handleCaptchaSuccess(response, config, tac) {
    tac.destroyWindow();
    captchaInstance = null;

    // 更新统计
    stats.total++;
    stats.success++;
    updateStats();

    // 显示成功结果
    showResultMessage("验证成功！", "success");
    showNotification("验证通过", "success");
}

/**
 * 验证失败回调
 */
function handleCaptchaFail(response, config, tac) {
    // 更新统计
    stats.total++;
    stats.fail++;
    updateStats();

    showResultMessage("验证失败，请重试", "fail");
    showNotification("验证失败", "error");

    // 重新加载验证码
    setTimeout(function () {
        if (tac) {
            tac.reloadCaptcha();
        }
    }, 1000);
}

/**
 * 显示结果消息
 */
function showResultMessage(message, type) {
    var $msg = $('#result-message');
    $msg.text(message)
        .removeClass('success fail')
        .addClass(type)
        .show();

    // 5秒后自动隐藏
    setTimeout(function () {
        $msg.fadeOut(300);
    }, 5000);
}

/**
 * 更新统计数据
 */
function updateStats() {
    $('#stat-total').text(stats.total);
    $('#stat-success').text(stats.success);
    $('#stat-fail').text(stats.fail);
}

/**
 * 显示通知
 */
function showNotification(message, type) {
    var $notification = $('#notification');
    $notification.text(message)
        .removeClass('notification-success notification-error notification-info')
        .addClass('notification-' + type)
        .addClass('show');

    setTimeout(function () {
        $notification.removeClass('show');
    }, 3000);
}
