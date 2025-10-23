$(".message-box").click(function (e) {
    e.stopPropagation();
});

$(".ringarea").click(function (e) {
    e.stopPropagation();
    $(".message-box").toggleClass("openalpha");
});

$(".ham4").on("click", function () {
    if ($(window).width() < 999) {
        $(".ham4").toggleClass("active");
        $(".pad-menu").slideToggle();
        $('.header-cont').toggleClass("active");
    } else {
        $(".ham4").removeClass("active");
        $(".header-cont").css("display", "flex");
        $('.header-cont').toggleClass("active");
    }
});

$(window).resize(function () {
    var windowWidth = $(window).width();

    if (windowWidth > 991) {
        $(".header-cont .left-box").css("display", "block");
        $(".header-cont .member-btn").css("display", "block");
    } else {
        $(".header-cont .left-box").css("display", "none");
        $(".header-cont .member-btn").css("display", "none");
    }
});

$(".mbbtn-1").on("click", function (event) {
    if ($(window).width() < 999) {
        $(this).next(".menu-2").slideToggle();
        $(this).toggleClass("now");
    }
});
$(".mbbtn-2").on("click", function (event) {
    if ($(window).width() < 999) {
        $(this).next(".menu-2").slideToggle();
        $(this).toggleClass("now");
    }
});

$(function () {
    $(".xx").on("click", function (event) {
        if (
            window.location.pathname !== "/search/" &&
            window.location.pathname.indexOf("/project/oversight") < 0
        ) {
            // exclude search/project_oversight page
            $(".pop-box").addClass("d-none");
            $("body").css("overflow", "initial");
        }
    });

    $(function () {
        gsap.registerPlugin(ScrollTrigger);

        ScrollTrigger.create({
            trigger: ".map-section",
            start: "top-=90% top",
            // markers: true,
            onEnter: function () {
                $(".map-section").addClass("vivi");
            },
        });
        ScrollTrigger.create({
            trigger: ".chart-section",
            start: "top-=80% top",
            // markers: true,
            onEnter: function () {
                $(".chart-section").addClass("vivi");
            },
        });
        ScrollTrigger.create({
            trigger: ".three-iconbox",
            start: "top-=75% top",
            // markers: true,
            onEnter: function () {
                $(".three-iconbox").addClass("vivi");
            },
        });
    });
});

// 以上為2023-09新切版

$(document).ready(function () {
    if (!document.cookie.includes("announcementread")) {
        $("#alert-content").removeClass("d-none");
    }

    $(".login-item").on("click", function () {
        $(".login-pop").removeClass("d-none");
    });

    $("li.active").removeClass("active");
    $('a[href="' + location.pathname + '"]')
        .closest(".nav-link")
        .addClass("active");

    $("#updateIsRead").on("click", function () {
        $.ajax({
            url: "/update_is_read",
            type: "GET",
            success: function () {
                $(".has-unread").hide();
            },
        });
    });

    // tooltip
    var tooltipTriggerList = [].slice.call(
        document.querySelectorAll('[data-bs-toggle="tooltip"]')
    );
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    $("#getAuth").on("click", function (e) {
        e.preventDefault();

        // Prevent multiple clicks
        if ($(this).data('requesting')) {
            return false;
        }
        $(this).data('requesting', true);

        let url =
            "https://orcid.org/oauth/authorize?client_id=APP-F6POVPAP5L1JOUN1&response_type=code&scope=/authenticate&redirect_uri=" +
            location.protocol +
            "//" +
            location.host +
            "/callback/orcid/auth?next=" +
            window.location.pathname;
        window.location.href = url;
    });

    $("#alert-box").on("click", function () {
        $.ajax({
            url: "/announcement_is_read",
            type: "GET",
            success: function (data) {
                $(".alert-content").hide();
                document.cookie =
                    "announcementread=" +
                    data.expired_time +
                    ";max-age=" +
                    data.expired_time +
                    "; path=/";
            },
        });
    });
});
