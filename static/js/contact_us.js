$(document).ready(function () {
    // Upload files
    $("#f-upload").change(function () {
        for (let i = 0; i < this.files.length; i++) {
            window.file_index += 1;
            let f = this.files[i];
            if ((window.f_total_size + f.size) / (1024 * 1024) > 20) {
                alert(
                    "檔案容量過大，已自動移除。\n\n注意：\n最大可接受的上傳檔案大小為 20MB。\n若您的檔案超過此大小，請將其壓縮為 ZIP 檔案後再重新上傳。"
                );
                $("#f-list").append(
                    `<li class="d-flex align-items-center mb-2"><p class="f-label">${f.name}</p> <span class="notice ms-2">檔案過大，已移除 </span></li>`
                );
            } else if (f.size / (1024 * 1024) > 20) {
                alert(
                    "檔案容量過大，已自動移除。\n\n注意：\n最大可接受的上傳檔案大小為 20MB。\n若您的檔案超過此大小，請將其壓縮為 ZIP 檔案後再重新上傳。"
                );
                $("#f-list").append(
                    `<li class="d-flex align-items-center mb-2"><p class="f-label">${f.name}</p> <span class="notice ms-2">檔案過大，已移除 </span></li>`
                );
            } else {
                $("#f-list").append(`<li class="d-flex align-items-center mb-2">
          <p class="f-label">${f.name}</p>
          <button type="button" class="delete-file-btn" data-index="${window.file_index}">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 18.828 18.828">
              <g data-name="Group 688" transform="translate(-1823.086 -445.086)">
                <line data-name="Line 1" x1="16" y2="16" transform="translate(1824.5 446.5)" fill="none" stroke="#257455" stroke-linecap="round" stroke-width="2"/>
                <line data-name="Line 2" x2="16" y2="16" transform="translate(1824.5 446.5)" fill="none" stroke="#257455" stroke-linecap="round" stroke-width="2"/>
              </g>
            </svg>
          </button>
        </li>`);
                window.file_list[window.file_index] = { file: f };
                window.f_data.append("uploaded_file", f, f.name);
                window.f_total_size += f.size;
            }
        }
        $(".delete-file-btn")
            .off("click")
            .on("click", function (event) {
                const dataIndex = $(this).data("index");
                if (window.file_list[dataIndex]) {
                    window.f_total_size -=
                        window.file_list[dataIndex]["file"].size;
                    delete window.file_list[dataIndex];
                    // Clear and rebuild FormData
                    window.f_data = new FormData();
                    Object.entries(window.file_list).forEach(([k, v]) => {
                        if (v !== undefined) {
                            window.f_data.append(
                                "uploaded_file",
                                v["file"],
                                v["file"].name
                            );
                        }
                    });
                    $(this).parent().remove();
                }
            });
    });

    // 初始化變數
    window.file_index = 0;
    window.file_list = {};
    window.f_data = new FormData();
    window.f_total_size = 0;

    // Switch checkbox
    const checkboxes = document.querySelectorAll(".check-list li");
    checkboxes.forEach((checkbox) => {
        checkbox.addEventListener("click", function () {
            console.log("Checkbox clicked");
            const itemsWithNowClass =
                document.querySelectorAll(".check-list li.now");
            itemsWithNowClass.forEach((item) => {
                item.classList.remove("now");
            });

            const listItem = this.closest("li");
            listItem.classList.add("now");
        });
    });

    // Submit the question
    $(document).on("submit", "form", function (event) {
        $(".loading-pop").removeClass("d-none");
        event.preventDefault();

        window.f_data = new FormData();
        let otherFormData = new FormData($("#submitForm")[0]);
        for (var pair of otherFormData.entries()) {
            window.f_data.append(pair[0], pair[1]);
        }

        $.ajax({
            url: $(this).attr("action"),
            type: $(this).attr("method"),
            dataType: "JSON",
            data: window.f_data,
            processData: false,
            contentType: false,
            success: function (data, status) {
                $(".loading-pop").addClass("d-none");
                alert("請求已送出");
                //window.f_data = new FormData();
            },
            error: function (xhr, desc, err) {
                $(".loading-pop").addClass("d-none");
                alert("未知錯誤，請聯繫管理員");
                //window.f_data = new FormData();
            },
        });
    });

    // Validate input
    $(".submit").on("click", function () {
        console.log("submit clicked");

        $(".is-invalid").removeClass("is-invalid");
        let checked = true;

        if (
            !ValidateEmail($("input[name=email]").val()) ||
            $("textarea[name=description]").val() == ""
        ) {
            checked = false;
            $(".info-pop-2").removeClass("d-none");
            $("body").css("overflow", "hidden");

            if ($("input[name=email]").val() == "") {
                $("input[name=email]").addClass("is-invalid");
                $(".mail-error").show();
                $(".mail-error-icon").show();
            } else {
                $(".title-error").hide();
                $(".title-error-icon").hide();
            }

            if ($("textarea[name=description]").val() == "") {
                $("textarea[name=description]").addClass("is-invalid");
                $(".description-error").show();
                $(".description-error-icon").show();
            } else {
                $(".description-error").hide();
                $(".description-error-icon").hide();
            }
        }

        if (checked) {
            $("#submitForm").submit();
        }

        $(".xx").on("click", function (event) {
            $(".pop-box").addClass("d-none");
            $("body").css("overflow", "initial");
        });
    });

    function ValidateEmail(inputText) {
        let mailformat =
            /(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])/;
        if (inputText.match(mailformat)) {
            return true;
        } else {
            return false;
        }
    }
});
