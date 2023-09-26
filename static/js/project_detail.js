var $csrf_token = $('[name="csrfmiddlewaretoken"]').attr('value');
let pk = $('input[name=pk]').val();

const allEqual = arr => arr.every(v => v === arr[0])

$.ajax({
  type: 'GET',
  url: `/api/get_project_detail/?pk=${pk}`,
  success: function (response) {
    window.sa_list = response.sa_list
    window.sa_d_list = response.sa_d_list
    window.projects = response.projects
    window.editable = response.editable
  }
})

$("#edit-project").autocomplete({
  minLength: 0,
  // source: window.projects,
  source: function (request, response) {
    $.ajax({
      type: 'GET',
      url: `/api/get_project_detail/?pk=${pk}`,
      success: function (data) {
        response($.map(data.projects, function (item) {
          return {
            label: item.label,  //列表所顯示的文字
            value: item.value, 	//列表選項的值
          };
        }));
      }
    });
  },
  change: function (event, ui) {
    $("#edit-project").val((ui.item ? ui.item.label : ""));
    $("#edit-project_id").val((ui.item ? ui.item.value : ""));
    if ($("#edit-project").val() == '') {
      $('#edit-deployment, #edit-deployment_id, #edit-studyarea, #edit-studyarea_id').val('')
      $sa.autocomplete('option', 'source', '');
      $dep.autocomplete('option', 'source', '');
    }
  },
  select: function (event, ui) {
    $("#edit-project_id").val(ui.item.value);
    $("#edit-project").val(ui.item.label)
    $.ajax({
      data: { 'pk': $("#edit-project_id").val() },
      type: "POST",
      url: "/update_edit_autocomplete",
      headers: { 'X-CSRFToken': $csrf_token },
      success: function (data) {
        // 修改studyarea & deployment
        $sa.autocomplete('option', 'source', data.sa_list);
        $dep.autocomplete('option', 'source', '');
        window.sa_d_list = data.sa_d_list;
        $('#edit-deployment, #edit-deployment_id, #edit-studyarea, #edit-studyarea_id').val('')
      },
      error: function () {
        alert('未知錯誤，請聯繫管理員');
      }
    })

    return false;
  }
}).focus(function () {
  $(this).autocomplete("search", "");
}).val($('input[name=project-name]').val())



// dependent dropdown menu
var $dep = $("#edit-deployment").autocomplete({
  source: [],
  minLength: 0,
  change: function (event, ui) {
    // only allow deployments in the list
    $(this).val((ui.item ? ui.item.label : ""));
    $("#edit-deployment_id").val((ui.item ? ui.item.value : ""));
  },
  select: function (event, ui) {
    $("#edit-deployment").val(ui.item.label);
    $("#edit-deployment_id").val(ui.item.value);
    return false;
  }
}).focus(function () {
  $(this).autocomplete("search", "");
});

$sa = $("#edit-studyarea").autocomplete({
  minLength: 0,
  source: function (request, response) {
    $.ajax({
      type: 'GET',
      url: `/api/get_project_detail/?pk=${pk}`,
      success: function (data) {
        response($.map(data.sa_list, function (item) {
          return {
            label: item.label,  //列表所顯示的文字
            value: item.value, 	//列表選項的值
          };
        }));
      }
    });
  },
  open: function (event, ui) {
    window.pre_select = $('#edit-studyarea').val();
  },
  change: function (event, ui) {
    // only allow studyarea in the list
    $("#edit-studyarea").val((ui.item ? ui.item.label : ""));
    $("#edit-studyarea_id").val((ui.item ? ui.item.value : ""));
    if ($("#edit-studyarea").val() == '') {
      $('#edit-deployment, #edit-deployment_id').val('')
      $dep.autocomplete('option', 'source', '');
    }
  },
  select: function (event, ui) {
    $("#edit-studyarea_id").val(ui.item.value);
    $("#edit-studyarea").val(ui.item.label)
    if (pre_select != ui.item.label) {
      $('#edit-deployment, #edit-deployment_id').val('')
    }
    var src = ui.item.label;
    // 這邊會跟著改
    $dep.autocomplete('option', 'source', window.sa_d_list[src]);
    return false;
  }
}).focus(function () {
  $(this).autocomplete("search", "");
})



//https://emailregex.com

function ValidateEmail(inputText) {
  let mailformat = /(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])/
  if (inputText.match(mailformat)) {
    $('#email-check').attr('fill', 'green');
    $('button.download').prop('disabled', false);
  } else {
    $('#email-check').attr('fill', 'lightgrey');
    $('button.download').prop('disabled', true);
  }
}

function updateTable(page, page_from) {

  $(".loading-pop").removeClass("d-none");

  let speciesArray = [];
  if ($(`ul.species-check-list li.now.all`).length == 0) {
    let check_list = $(`ul.species-check-list li.now:not(.all)`);
    check_list.each(function () {
      if ($(this).data("species") != undefined) {
        speciesArray.push($(this).data("species"));
      }
    });
  }

  let saArray = [];
  if ($(`ul.studyarea-list li.now.all-sa`).length == 0) {
    let check_list = $(`ul.studyarea-list li.now:not(.all-sa)`);
    check_list.each(function () {
      if ($(this).data("sa") != undefined) {
        saArray.push($(this).data("sa"));
      }
    });
  }

  $.ajax({
    type: "POST",
    url: "/api/data",
    data: {
      pk: pk,
      limit: $(`.page-inf select[name=limit]`).val(),
      page: page,
      orderby: $(".now-order").data("order"),
      sort: $(".now-order").hasClass("downar") ? "asc" : "desc",
      times: $("input[name=times]").val(),
      // pk: $("input[name=pk]").val(),
      species: speciesArray,
      studyarea: saArray,
      start_altitude: $("input[name=start_altitude]").val(),
      end_altitude: $("input[name=end_altitude]").val(),
      start_date: $("input[name=start_date]").val(),
      end_date: $("input[name=end_date]").val(),
      folder_name: $('#select-folder option:selected').val(),
      county_name: $('#select-county option:selected').val(),
      protectarea_name: $('#select-protectarea option:selected').val(),
      deployment: $('input[name="d-filter"]:checked').map(function () { return $(this).val(); }).get(),
    },
    headers: { "X-CSRFToken": $csrf_token },
    success: function (response) {
      $(".loading-pop").addClass("d-none");

      $(`.phototable tr.data-rows`).remove();
      let i;
      for (i = 0; i < response.data.length; i++) {
        // keyword & funding agency
        $(".phototable").append(`
                        <tr class="data-rows" data-image_id="${response.data[i]['image_id']}" data-image_uuid="${response.data[i]['image_uuid']}"
                         data-saname="${response.data[i]["saname"]}"  data-dname="${response.data[i]["dname"]}" data-filename="${response.data[i]["filename"]}"
                         data-datetime="${response.data[i]["datetime"]}" data-species="${response.data[i]["species"]}" data-life_stage="${response.data[i]["life_stage"]}"
                         data-sex="${response.data[i]["sex"]}" data-antler="${response.data[i]["antler"]}" data-animal_id="${response.data[i]["animal_id"]}" data-remarks="${response.data[i]["remarks"]}">
                            <td class="d-none del-check">
                              <input type="checkbox" class="inp-check edit-checkbox" name="edit" value="${response.data[i]['image_id']}" data-uuid="${response.data[i]['image_uuid']}">
                            </td>
                            <td>${response.data[i]["saname"]}</td>
                            <td>${response.data[i]["dname"]}</td>
                            <td>${response.data[i]["filename"]}</td>
                            <td>${response.data[i]["datetime"]}</td>
                            <td>${response.data[i]["species"]}</td>
                            <td>${response.data[i]["life_stage"]}</td>
                            <td>${response.data[i]["sex"]}</td>
                            <td>${response.data[i]["antler"]}</td>
                            <td>${response.data[i]["animal_id"]}</td>
                            <td>${response.data[i]["remarks"]}</td>
                            <td>${response.data[i]["file_url"]}</td>
                        </tr>`);
      }


      // 預設disable
      $('.e-button, .d-button').addClass('disabled')
      //編輯 click
      $('input[name="edit"]').not('#edit-all').off('click')
      $('input[name="edit"]').on('click', function () {
        if ($("input[name='edit']").is(":checked")) {
          $('.e-button, .d-button').removeClass('disabled')
        } else {
          $('.e-button, .d-button').addClass('disabled')
        }
      })

      // 如果編輯模式開啟 把checkbox那欄打開
      if ($('#edit_button').data('edit') == 'on') {
        $('.data-rows .del-check').removeClass('d-none')
        // 如果本來勾選編輯全部 要把下方的checkbox也勾選 且打開編輯及刪除按鈕
        if ($('input[name="edit"]#edit-all').is(":checked")) {
          $("input[name='edit']").prop('checked', true)
        }      
        $('.e-button, .d-button').removeClass('disabled')
      }

      // 影像
      // lazy loading for images
      var watcher = new IntersectionObserver(onEnterView);
      var lazyImages = document.querySelectorAll("img.lazy");
      for (let image of lazyImages) {
        watcher.observe(image); // 開始監視
      }
      function onEnterView(entries, observer) {
        for (let entry of entries) {
          if (entry.isIntersecting) {
            var img = entry.target;
            img.setAttribute("src", img.dataset.src);
            observer.unobserve(img);
          }
        }
      }

      // lazy loading for videos
      var watcher2 = new IntersectionObserver(onEnterView2);
      var lazyVideos = document.querySelectorAll("video");
      for (let v of lazyVideos) {
        watcher2.observe(v); // 開始監視
        v.removeAttribute('controls');
      }
      function onEnterView2(entries, observer) {
        for (let entry of entries) {
          if (entry.isIntersecting) {
            var video = entry.target;
            video.setAttribute("preload", "");
            observer.unobserve(video);
          }
        }
      }

      // event listener for loading video & img
      $('img').on('error', function (event) {
        $(this).parent().html('<p align="center" class="cannot-load">無法載入</p>')
      })

      $('video source').on('error', function (event) {
        $(this).parent().parent().html('<p align="center" class="cannot-load">無法載入</p>')
      })

      // 修改筆數資數

      $('.page-inf').removeClass('d-none')
      /* 這邊要修改成當前狀況 */
      $(`.page-inf span.show-start`).html(response.show_start);
      $(`.page-inf span.show-end`).html(response.show_end);
      $(`.page-inf span.show-total`).html(response.total);

      // 修改頁碼

      // 把之前隱藏的部分拿掉
      $(`.page-inf .d-none`).removeClass("d-none");
      $(`.page-inf .pt-none`).removeClass("pt-none");


      // 修改上下一頁
      if (page - 1 > 0) {
        $(`.page-inf .back`).data("page", page - 1);
      } else {
        $(`.page-inf .back`).addClass("pt-none");
      }

      if (page + 1 <= response.total_page) {
        $(`.page-inf .next`).data("page", page + 1);
      } else {
        $(`.page-inf .next`).addClass("pt-none");
      }

      // 修改最後一頁
      $(`.page-inf .final_page`).data("page", response.total_page);
      $(`.page-inf .final_page`).html(response.total_page);

      // 如果只有一頁 要把data-page=1 & 最後一頁隱藏
      if (response.total_page <= 1) {
        $(`.page-inf .final_page, .page-inf .first_page`).addClass("d-none");
      }

      // 如果都沒有 要把上下頁隱藏
      if (response.total_page == 0) {
        $(`.page-inf .back, .page-inf .next`).addClass("d-none");
      }

      // 修改中間頁碼
      $(`.page-inf .middle_page`).remove();

      let html = "";
      for (let i = 0; i < response.page_list.length; i++) {
        if (response.page_list[i] == page) {
          // 如果等於現在的頁數 要加上now
          html += ` <a class="middle_page num now changePage" data-page="${response.page_list[i]}">${response.page_list[i]}</a> `;
        } else {
          html += ` <a class="middle_page num changePage" data-page="${response.page_list[i]}">${response.page_list[i]}</a>  `;
        }
      }

      $(`.page-inf .back`).after(html);

      $(".changePage").off("click");
      $(".changePage").on("click", function () {
        updateTable($(this).data("page"))
      });

      // 預設為第一張
      // console.log($('.data-rows '))
      if (page_from == 'back') {
        changeEditContent($('tr.data-rows').last());
      } else if (page_from == 'next') {
        changeEditContent($('tr.data-rows').first());
      }

      // $('.phototable .data-rows').on('click',function (event) {
      //   $('.photode-pop').removeClass('d-none');
      // });


      $('.data-rows td:not(:first-child)').on('click', function () {
        // let current_row = $(this);
        // let idx = table.column(current_row).index();
        $('.photode-pop').removeClass('d-none');
        $('body').css("overflow", "hidden");

        changeEditContent($(this).parent());
        $('.edit-prev, .edit-next').removeClass('d-none');
      });


      // 跳到表格最上方
      $([document.documentElement, document.body]).animate({
        scrollTop: $(".innbox").offset().top
      }, 200);


    },
    error: function () {
      $(".loading-pop").addClass("d-none");
    },
  });

}


$(document).ready(function () {


  // 取消按鈕
  $('#canceledit').on('click', function(){
    $('.photode-pop').addClass('d-none')   
    $('body').css("overflow", "initial");

  })

  $('.calcel-remove').on('click', function(){
    $('.remove-pop').addClass('d-none')   

  })


  // 刪除
  $('#deleteButton').on('click', function () {
    $('.remove-pop').removeClass('d-none')
  })

  $('#deleteData').on('click', function () {


    checkedvalue = [];
    checkeduuid = [];
    $("input[name=edit]").not('#edit-all').each(function () {
      if ($(this).is(":checked")) {
        if (!isNaN($(this).val())) {
          checkedvalue.push($(this).val())
          checkeduuid.push($(this).data('uuid'));
        }
      }
    });
    // $('#deleteModal').modal('hide')
    // ajax to delete data
    $('.remove-pop').addClass('d-none')
    $.ajax({
      data: { 'image_id': checkedvalue, 'image_uuid': checkeduuid },
      headers: { 'X-CSRFToken': $csrf_token },
      type: "POST",
      url: "/delete/" + pk + '/',
      success: function (data) {
        if (data.return_mesg) {
          alert('欲刪除的資料含有原始照片，故未完全刪除。如需刪除原始照片，請聯絡系統管理員或計畫總管理人')
        }


        updateTable($('.changePage.now').data('page'))

        // 記錄原本的物種
        let speciesArray = [];
        let check_list = $(`ul.species-check-list li.now:not(.all)`);
        check_list.each(function () {
          if ($(this).data("species") != undefined) {
            speciesArray.push($(this).data("species"));
          }
        });

        // update filter //
        $(".species-check-list li:not(.all)").remove()
        for (let i = 0; i < data['species'].length; i++) {
          //如果本來就check 加上now
          let now_str = ''
          if (speciesArray.includes(data['species'][i]['name'])) {
            now_str = 'now'
          }
          $('.species-check-list li.all').after(`
            <li class="${now_str}" data-species="${data['species'][i]['name']}">
            <div class="cir-checkbox">
              <img class="coricon" src="/static/image/correct.svg">
            </div>
            <p>${data['species'][i]['name']} (${data['species'][i]['count']})</p>
            </li>
          `)
        }

        // bind event
        $(".species-check-list li:not(.all)").click(function () {
          $(this).toggleClass("now");
          $(`.species-check-list li.all`).removeClass("now");
        });

      },
      error: function () {
        alert('未知錯誤，請聯繫管理員');
      }
    })

  })

  $('.pop-box .xx').on('click', function (event) {
    $(this).parent().parent().parent().addClass('d-none');
  });


  $('.opitem-btn').on('click', function () {
    if ($('.left-selectlist').css("left") == "0px") {
      $('.left-selectlist').animate({
        left: "-300"
      });
    } else {
      $('.left-selectlist').animate({
        left: "0"
      });
    }
  });

  /* 日期篩選設定 */

  let date_locale = {
    days: ['周日', '周一', '周二', '周三', '周四', '周五', '周六'],
    daysShort: ['日', '一', '二', '三', '四', '五', '六'],
    daysMin: ['日', '一', '二', '三', '四', '五', '六'],
    months: ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月'],
    monthsShort: ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月'],
    today: '今天',
    clear: '清除',
    dateFormat: 'yyyy-MM-dd',
    timeFormat: 'HH:mm',
    firstDay: 1
  }

  let start_date_picker = new AirDatepicker('#start_date', { locale: date_locale });
  let end_date_picker = new AirDatepicker('#end_date', { locale: date_locale });


  $('.show_start').on('click', function () {
    if (start_date_picker.visible) {
      start_date_picker.hide();
    } else {
      start_date_picker.show();
    }
  })

  $('.show_end').on('click', function () {
    if (end_date_picker.visible) {
      end_date_picker.hide();
    } else {
      end_date_picker.show();
    }
  })

  // 篩選標題開合
  $('.settitle-box').on('click', function () {
    $(this).next('.check-list').slideToggle();
    $(this).toggleClass('now');
  });



  // 表格排序

  $('.upar').on('click', function () {
    $(".upar").css("fill", "#78d989");
    $(".now-order").removeClass("now-order");
    $(this).css("fill", "#FFF");
    $(this).addClass("now-order");
    $('.downar').css("fill", "#78d989");
    updateTable(1);
  });

  $('.downar').on('click', function () {
    $(".downar").css("fill", "#78d989");
    $(".now-order").removeClass("now-order");
    $(this).addClass("now-order");
    $(this).css("fill", "#FFF");
    $('.upar').css("fill", "#78d989");
    updateTable(1);
  });


  /* 物種篩選控制 結束 */

  $(".species-check-list li:not(.all)").click(function () {
    $(this).toggleClass("now");
    $(`.species-check-list li.all`).removeClass("now");
  });

  // species: if 'all' checked, check all checkbox

  $(".species-check-list li.all").click(function () {

    if ($(this).hasClass("now")) {
      // 移除掉全部的
      $(this).removeClass("now");
      $(`.species-check-list li`).removeClass("now");
    } else {
      // 先移除掉全部的再一次加上去
      $(this).removeClass("now");
      $(`.species-check-list li`).removeClass("now");
      $(this).addClass("now");
      $(`.species-check-list li`).addClass("now");
    }
  });

  /* 樣區 & 相機位置 控制 */

  // 樣區開合
  $('.sa-title p').on('click', function (e) {
    $(this).next('.arrup').toggleClass('close')
    $(this).parent().next('.check2-layerbox').toggleClass('d-none')
  })

  $('.sa-title .arrup').on('click', function (e) {
    $(this).toggleClass('close')
    $(this).parent().next('.check2-layerbox').toggleClass('d-none')
  })


  // 選擇所有樣區
  $('.all-sa').on('click', function () {
    $(this).toggleClass('now')
    if ($(this).hasClass('now')) {
      $('.studyarea-list li').addClass('now')
      $('.studyarea-list li input').prop("checked", true);

    } else {
      $('.studyarea-list li').removeClass('now')
      $('.studyarea-list li input').prop("checked", false);
    }
  })

  $('.dep-checkbox p').on('click', function () {
    $(this).prev('input[type=checkbox]').trigger('click');
  })

  // 選擇樣區底下的所有相機位置 
  $('.sa-title .cir-checkbox').on('click', function () {
    let sa = $(this).parent().parent().data('sa')
    if ($(this).parent().parent().hasClass('now')) {
      $(`li[data-parent_sa=${sa}] input`).prop("checked", false);
    } else {
      $(`li[data-parent_sa=${sa}] input`).prop("checked", true);
    }

    $(this).parent().parent().toggleClass('now')

  })

  $('.dep-checkbox.all').on('click', function () {
    let sa = $(this).data('parent_sa')
    if ($(this).find('input[type=checkbox]').is(":checked")) {
      $(`li[data-parent_sa=${sa}] input`).prop("checked", true);
      // 整個樣區的check icon
      $(`li[data-sa=${sa}]`).addClass('now')
    } else {
      // 整個樣區的check icon拿掉
      $(`li[data-sa=${sa}]`).removeClass('now')
      $(`li[data-parent_sa=${sa}] input`).prop("checked", false);
    }
  })


  $('.dep-checkbox').on('click', function () {
    let sa = $(this).data('parent_sa')
    if ($(`li[data-sa=${sa}] input:checked`).length > 0) {
      $(`li[data-sa=${sa}]`).addClass('now')
    } else {
      $(`li[data-sa=${sa}]`).removeClass('now')
    }
  })

  /* 樣區 & 相機位置 結束 */

  $("#select-folder").select2({language: "zh-TW"})
  $("#select-protectarea").select2({language: "zh-TW"})
  $("#select-county").select2({language: "zh-TW"})


  /* 進來頁面後取得起始資料 */

  updateTable(1)

  // 每頁顯示筆數
  $("select[name=limit]").on("change", function () {
    updateTable(1);
  });

  // 時鐘
  $('.icon-clock').on('click', function () {
    $('input[name=times]').trigger('click')
  })

  // 篩選按鈕
  $('#submitSelect').on('click', function () {
    updateTable(1)
  })

  // 清除按鈕
  $('.clear').on('click', function () {

    // 樣區
    // 全部拿掉再全部加上去
    $('ul.studyarea-list li').removeClass('now')
    $('ul.studyarea-list li').addClass('now')
    // checkbox
    $('.studyarea-list li input').prop("checked", true);

    // 物種
    // 全部拿掉再全部加上去
    $('ul.species-check-list li').removeClass('now')
    $('ul.species-check-list li').addClass('now')
    

    $("input[name=start_altitude]").val('')
    $("input[name=end_altitude]").val('')

    $("input[name='start_date']").val('')
    $("input[name='end_date']").val('')

    // folder, protectarea, county
    $("#select-folder").val(null).trigger('change');
    $("#select-protectarea").val(null).trigger('change');
    $("#select-county").val(null).trigger('change');

    // 拍攝時間
    $("input[name=times]").val('')
  });


  // 下載篩選資料 先確認是否有完成email填寫

  $('#downloadButton').on('click', function () {

    $.ajax({
      type: "POST",
      url: "/api/check_login/",
      headers: { 'X-CSRFToken': $csrf_token },
      success: function (response) {

        if (response.redirect) {
          if (response.messages) {
            alert(response.messages);
            window.location.replace(window.location.origin + "/personal_info");
          } else {
            // $('#downloadModal').modal('show')
            $('.down-pop').removeClass('d-none');
          }
        } else {
          if (response.messages) {
            alert(response.messages);
            $('.login-pop').removeClass('d-none')
          }
          else {
            // $('#downloadModal').modal('show')
            $('.down-pop').removeClass('d-none');
          }
        }
      },
      error: function () {
        alert('未知錯誤，請聯繫管理員');
      }
    })
  })


  $('.down-pop .xx').on('click', function (event) {
    $('.down-pop').addClass('d-none');
  });

  $('#canceldownload').on('click', function (event) {
    $('.down-pop').addClass('d-none');
  });

  $("#download-email").keyup(function () {
    ValidateEmail($(this).val())
  });


  $('.download').on('click', function () {

    let pk = $('input[name=pk]').val();

    let speciesArray = [];
    if ($(`ul.studyarea-list li.now.all`).length == 0) {
      let check_list = $(`ul.species-check-list li.now:not(.all)`);
      check_list.each(function () {
        if ($(this).data("species") != undefined) {
          speciesArray.push($(this).data("species"));
        }
      });
    }

    let saArray = [];
    let check_list = $(`ul.studyarea-list li.now:not(.all-sa)`);
    check_list.each(function () {
      if ($(this).data("sa") != undefined) {
        saArray.push($(this).data("sa"));
      }
    });

    $.ajax({
      data: {
        email: $("input[name=email]").val(),
        times: $("input[name=times]").val(),
        species: speciesArray,
        start_altitude: $("input[name=start_altitude]").val(),
        end_altitude: $("input[name=end_altitude]").val(),
        start_date: $("input[name=start_date]").val(),
        end_date: $("input[name=end_date]").val(),
        folder_name: $('#select-folder option:selected').val(),
        county_name: $('#select-county option:selected').val(),
        protectarea_name: $('#select-protectarea option:selected').val(),
        deployment: $('input[name="d-filter"]:checked').map(function () { return $(this).val(); }).get(),
        sa: saArray
      },
      type: "POST",
      headers: { 'X-CSRFToken': $csrf_token },
      url: "/download/" + pk,
      success: function () {
        alert('請求已送出');
        $('.down-pop').addClass('d-none')
      },
      error: function () {
        alert('未知錯誤，請聯繫管理員');
        $('.down-pop').addClass('d-none')
      }
    })
  })




  // 編輯頁面的自動選項
  var species = ['水鹿', '山羌', '獼猴', '山羊', '野豬', '鼬獾', '白鼻心', '食蟹獴', '松鼠', '飛鼠', '黃喉貂', '黃鼠狼', '小黃鼠狼', '麝香貓', '黑熊', '石虎', '穿山甲', '梅花鹿', '野兔', '蝙蝠', '無法辨識', '空拍', '工作照', '測試', '台灣山鷓鴣', '台灣竹雞', '黑長尾雉', '藍腹鷴', '黑冠麻鷺', '環頸雉', '山鷸', '灰林鴿', '金背鳩', '珠頸斑鳩', '翠翼鳩', '黃痣藪眉', '台灣噪眉', '台灣紫嘯鶇', '虎鶇', '白眉鶇', '白腹鶇', '赤腹鶇', '白頭鶇'].sort()
  var antler = ['初茸', '茸角一尖', '茸角一岔二尖', '茸角二岔三尖', '茸角三岔四尖', '硬角一尖', '硬角一岔二尖', '硬角二岔三尖', '硬角三岔四尖', '解角']
  var sex = ['雄性', '雌性', '無法判定']
  var life_stage = ['成體', '亞成體', '幼體', '無法判定']

  $('#edit-species').autocomplete({
    minLength: 0,
    source: function (request, response) {
      var data = $.grep(species, function (value) {
        return value.substring(0, request.term.length).toLowerCase() == request.term.toLowerCase();
      });
      response(data);
    }
  }).focus(function () {
    $(this).autocomplete("search", "");
  });

  $('#edit-antler').autocomplete({
    minLength: 0,
    source: function (request, response) {
      var data = $.grep(antler, function (value) {
        return value.substring(0, request.term.length).toLowerCase() == request.term.toLowerCase();
      });
      response(data);
    }
  }).focus(function () {
    $(this).autocomplete("search", "");
  });

  $('#edit-sex').autocomplete({
    minLength: 0,
    source: function (request, response) {
      var data = $.grep(sex, function (value) {
        return value.substring(0, request.term.length).toLowerCase() == request.term.toLowerCase();
      });
      response(data);
    }
  }).focus(function () {
    $(this).autocomplete("search", "");
  });

  $('#edit-life_stage').autocomplete({
    minLength: 0,
    source: function (request, response) {
      var data = $.grep(life_stage, function (value) {
        return value.substring(0, request.term.length).toLowerCase() == request.term.toLowerCase();
      });
      response(data);
    }
  }).focus(function () {
    $(this).autocomplete("search", "");
  });



  $('#edit_button').on('click', function () {
    if ($('#edit_button').data('edit') == 'off') {
      $('#edit_button').data('edit', 'on');
      // console.log($($.fn.dataTable.tables(true)).DataTable().column(0))
      // $($.fn.dataTable.tables(true)).DataTable().column(0).visible(true);
      $('#edit_button').html(`<svg id="Group_749" data-name="Group 749" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="20" height="19.999" viewBox="0 0 20 19.999">
      <g id="Group_748" data-name="Group 748" clip-path="url(#clip-path)">
        <path id="Path_10217" data-name="Path 10217" d="M20,4.238a2.818,2.818,0,0,1-.855,2q-3.8,3.8-7.6,7.6-1.8,1.8-3.613,3.6a1.215,1.215,0,0,1-.45.279q-3.29,1.11-6.586,2.2a1.082,1.082,0,0,1-.4.078.546.546,0,0,1-.446-.786Q.775,17,1.512,14.792c.256-.769.509-1.54.774-2.306a1.037,1.037,0,0,1,.231-.384Q8.133,6.477,13.756.861A2.744,2.744,0,0,1,17.741.853q.734.724,1.46,1.457A2.747,2.747,0,0,1,20,4.238M7.447,16.318,17,6.767,13.233,3,3.678,12.549l3.768,3.769M17.837,5.967c.2-.192.414-.38.607-.587a1.622,1.622,0,0,0,.03-2.23c-.523-.565-1.071-1.108-1.634-1.633a1.578,1.578,0,0,0-2-.128,9.64,9.64,0,0,0-.828.753l3.824,3.825M6.4,16.925,3.073,13.6,1.406,18.587,6.4,16.925" transform="translate(0 0)" fill="#257455"/>
      </g>
    </svg>結束編輯`)
      // show buttons
      $('.d-button, .e-button').removeClass('d-none')
      // bind onclick event
      $('.del-check').removeClass('d-none')
    } else {
      $('#edit_button').data('edit', 'off');
      $('.del-check').addClass('d-none')
      // uncheck all
      // $($.fn.dataTable.tables(true)).DataTable().column(0).visible(false);
      $('#edit_button').html(`
        <svg id="Group_749" data-name="Group 749" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="20" height="19.999" viewBox="0 0 20 19.999">
        <g id="Group_748" data-name="Group 748" clip-path="url(#clip-path)">
          <path id="Path_10217" data-name="Path 10217" d="M20,4.238a2.818,2.818,0,0,1-.855,2q-3.8,3.8-7.6,7.6-1.8,1.8-3.613,3.6a1.215,1.215,0,0,1-.45.279q-3.29,1.11-6.586,2.2a1.082,1.082,0,0,1-.4.078.546.546,0,0,1-.446-.786Q.775,17,1.512,14.792c.256-.769.509-1.54.774-2.306a1.037,1.037,0,0,1,.231-.384Q8.133,6.477,13.756.861A2.744,2.744,0,0,1,17.741.853q.734.724,1.46,1.457A2.747,2.747,0,0,1,20,4.238M7.447,16.318,17,6.767,13.233,3,3.678,12.549l3.768,3.769M17.837,5.967c.2-.192.414-.38.607-.587a1.622,1.622,0,0,0,.03-2.23c-.523-.565-1.071-1.108-1.634-1.633a1.578,1.578,0,0,0-2-.128,9.64,9.64,0,0,0-.828.753l3.824,3.825M6.4,16.925,3.073,13.6,1.406,18.587,6.4,16.925" transform="translate(0 0)" fill="#257455"/>
        </g>
      </svg>
      編輯模式`)
      $('.d-button, .e-button').addClass('d-none')
    }
    // // adjust columns after 1000 ms
    // setTimeout(function () {
    //   $.fn.dataTable.tables({ visible: false, api: true }).columns.adjust();
    // }, 1000);
  })



  $('#edit-all').on('click', function () {
    if ($('#edit-all').is(':checked')) {
      $('.edit-checkbox').prop('checked', true)
    } else {
      $('.edit-checkbox').each(function () {
        $('.edit-checkbox').prop('checked', false)
      });
    }
  })



  // $('#editModal').on('hidden.bs.modal', function () {
  //   // remove next & prev event after modal close
  //   $(this).off('keydown');
  // })

  document.querySelector('#editForm').addEventListener('submit', (e) => {
    e.preventDefault();
  });



  // 按表格左方「編輯」按鈕
  $('.e-button').on('click', function () {
    let img_array = []
    let imguuid_array = []
    let sa_array = []
    let dep_array = []
    let species_array = []
    let sex_array = []
    let life_stage_array = []
    let antler_array = []
    let animal_id_array = []
    let remarks_array = []


    // TODO 這邊還沒做完
    $("input.edit-checkbox:checked").not('#edit-all').each(function () {
      // if (!$(this).parent().hasClass("dataTables_sizing")) {
      current_row = $(this).parent().parent();
      img_array.push(current_row.data('image_id'))
      imguuid_array.push(current_row.data('image_uuid'))
      sa_array.push(current_row.data('saname'))
      dep_array.push(current_row.data('dname'))
      species_array.push(current_row.data('species'))
      sex_array.push(current_row.data('sex'))
      life_stage_array.push(current_row.data('life_stage'))
      antler_array.push(current_row.data('antler'))
      animal_id_array.push(current_row.data('animal_id'))
      remarks_array.push(current_row.data('remarks'))

    });

    // if (img_array.length > 1) { // TODO 或是直接按row
    //   $('.edit-prev, .edit-next').addClass('d-none');
    //   $('#editModal').off('keydown');
    // } else {
    //   $('.edit-prev, .edit-next').removeClass('d-none');
    //   // 切換上下張的功能
    //   let c_row = $(this).parent()
    //   let idx = table.column(c_row).index();
    //   changeEditContent(c_row.parent(), idx);
    // }
    // }


    $('#edit-image_id').val(img_array)
    // remove notice info
    $('#edit-studyarea, #edit-deployment, #edit-project').removeClass('notice-border')
    $('.notice').addClass('d-none');
    // clean studyarea & deployment id
    $('#edit-studyarea_id').val('')
    $('#edit-deployment_id').val('')

    $('#edit-project').val($('input[name=project-name]').val());
    $('#edit-project_id').val(pk);
    $sa.autocomplete('option', 'source', window.sa_list);

    if (allEqual(sa_array)) {
      $('#edit-studyarea').val(sa_array[0])
      $dep.autocomplete('option', 'source', window.sa_d_list[current_row['saname']]);
    } else {
      $('#edit-studyarea').val('')
      $dep.autocomplete('option', 'source', '');
    }
    allEqual(dep_array) ? $('#edit-deployment').val(dep_array[0]) : $('#edit-deployment').val('');
    allEqual(species_array) ? $('#edit-species').val(species_array[0]) : $('#edit-species').val('');
    allEqual(life_stage_array) ? $('#edit-life_stage').val(life_stage_array[0]) : $('#edit-life_stage').val('');
    allEqual(sex_array) ? $('#edit-sex').val(sex_array[0]) : $('#edit-sex').val('');
    allEqual(antler_array) ? $('#edit-antler').val(antler_array[0]) : $('#edit-antler').val('');
    allEqual(animal_id_array) ? $('#edit-animal_id').val(animal_id_array[0]) : $('#edit-animal_id').val('');
    allEqual(remarks_array) ? $('#edit-remarks').val(remarks_array[0]) : $('#edit-remarks').val('');

    // image or videos
    if (allEqual(imguuid_array)) {

      $('#edit-filename').html(current_row.data('filename'))
      $('#edit-datetime').html(current_row.data('datetime'))
      $('#edit-image').html(current_row.find('td').last().html())
      // 上下張按鈕控制
      $('.photode-pop .arl, .photode-pop .arr').removeClass('d-none')
      $('.photode-pop .arr').unbind('click');
      $('.photode-pop .arr').on('click', function () {
        if (current_row.next('tr').length != 0) {
          changeEditContent(current_row.next('tr'));
        } else {
          updateTable($(`.page-inf .next`).data('page'), 'next')
        }
      })

      $('.photode-pop .arl').unbind('click');
      $('.photode-pop .arl').on('click', function () {
        if (current_row.prev('tr').length != 0) {
          changeEditContent(current_row.prev('tr'));
        } else {
          updateTable($(`.page-inf .back`).data('page'), 'back')
        }
      })
    } else {
      $('#edit-filename').html('')
      $('#edit-datetime').html('')
      $('#edit-image').html('')
      // 隱藏上下張按鈕
      $('.photode-pop .arl, .photode-pop .arr').addClass('d-none')
      $(document).off('keydown')

    }

    if ($('#edit-image video').length) {
      $("#edit-image video").prop("controls", true);
    }

    if ($('#edit-image img').length) {
      $('#edit-image .img').attr('src', $('#edit-image .img').data('src')).addClass('w-100').addClass('h-auto');
    }

    $('#edit-image video source').on('error', function (event) {
      $(this).parent().parent().html('<p class="cannot-load" align="center">無法載入</p>')
    })
    $('#edit-image video source, #edit-image img').on('error', function (event) {
      $(this).parent().html('<p class="cannot-load" align="center">無法載入</p>')
    })


    // $('#editModal').modal('show');
    $('.photode-pop').removeClass('d-none');
    $('body').css("overflow", "hidden");

    // disable edit

    let editable = window.editable;
    if ((editable != true) || ($('#edit_button').data('edit') == 'off')) {
      $('.edit-content input').attr('disabled', 'disabled')
      $('.edit-footer').addClass('d-none')
    } else {
      $('.edit-content input').prop("disabled", false)
      $('.edit-footer').removeClass('d-none')
    }


  })

  // 編輯後送出按鈕

  $('.edit-submit').on('click', function () {
    // // 記錄原本在什麼folder
    // let selected_folder = $('#select-folder option:selected').val();

    let checked = true
    // project
    if (!$('#edit-project').val()) {
      checked = false
      $('#edit-project').parent().next('.notice').removeClass('d-none')
      $('#edit-project').addClass('notice-border')
    }

    // studyarea
    if (!$('#edit-studyarea').val()) {
      checked = false
      $('#edit-studyarea').parent().next('.notice').removeClass('d-none')
      $('#edit-studyarea').addClass('notice-border')
    }
    // deployment
    if (!$('#edit-deployment').val()) {
      checked = false
      $('#edit-deployment').parent().next('.notice').removeClass('d-none')
      $('#edit-deployment').addClass('notice-border')
    }
    // datetime
    // if (!$('input[name=datetime]').val()){
    //   checked = false
    //   $('input[name=datetime]').next('.notice').removeClass('d-none')
    //   $('input[name=datetime]').addClass('notice-border')
    // }
    if (checked) {
      $.ajax({
        data: $('#editForm').serialize(),
        type: "POST",
        url: "/api/edit_image/" + pk,
        success: function (data) {
          // $('#editModal').modal('hide');
          $('.photode-pop').addClass('d-none')
          $('body').css("overflow", "initial");

          // 修改folder

          // $('#select-folder').select2('destroy').empty()

          // // 要重新選擇 如果原本的folder還在就選，不在就清空
          // has_selected = false
          // for (let i = 0; i < data.folder_list.length; i++) {
          //   $('#select-folder').append(`
          //       <option value="${ data.folder_list[i]['folder_name'] }">
          // 						${ data.folder_list[i]['folder_name'] } (最後更新：${ data.folder_list[i]['folder_last_updated'] }}
          // 			</option>
          //   `)
          //   if (data.folder_list[i]['folder_name'] == selected_folder) {
          //     has_selected = true
          //   }
          // }

          // if (has_selected){
          //   $('#select-folder').val(selected_folder).trigger('change');           
          // }

          updateTable($('.changePage.now').data('page'))

          // 記錄原本的物種
          let speciesArray = [];
          let check_list = $(`ul.species-check-list li.now:not(.all)`);
          check_list.each(function () {
            if ($(this).data("species") != undefined) {
              speciesArray.push($(this).data("species"));
            }
          });

          // update filter //
          $(".species-check-list li:not(.all)").remove()
          for (let i = 0; i < data['species'].length; i++) {
            //如果本來就check 加上now
            let now_str = ''
            if (speciesArray.includes(data['species'][i]['name'])) {
              now_str = 'now'
            }
            $('.species-check-list li.all').after(`
            <li class="${now_str}" data-species="${data['species'][i]['name']}">
            <div class="cir-checkbox">
              <img class="coricon" src="/static/image/correct.svg">
            </div>
            <p>${data['species'][i]['name']} (${data['species'][i]['count']})</p>
            </li>
          `)
          }

          // bind event
          $(".species-check-list li:not(.all)").click(function () {
            $(this).toggleClass("now");
            $(`.species-check-list li.all`).removeClass("now");
          });


        },
        error: function () {
          alert('未知錯誤，請聯繫管理員');
        }
      })
    }
  });



})


function changeEditContent(row) {

  // console.log(row)
  // remove notice info
  $('#edit-studyarea, #edit-deployment, #edit-project').removeClass('notice-border')
  $('.notice').addClass('d-none');
  // clean studyarea & deployment id
  $('#edit-studyarea_id').val('')
  $('#edit-deployment_id').val('')


  $('#edit-project').val($('input[name=project-name]').val())
  $('#edit-project_id').val(pk)
  $sa.autocomplete('option', 'source', window.sa_list);
  // $dep.autocomplete('option', 'source', response.sa_d_list[row['saname']]);
  $dep.autocomplete('option', 'source', window.sa_d_list[row.data('saname')]);
  $('#edit-studyarea').val(row.data('saname'))
  $('#edit-deployment').val(row.data('dname'))
  $('#edit-filename').html(row.data('filename'))
  $('#edit-datetime').html(row.data('datetime'))
  //$('#edit-datetime').val(row['datetime'].replace(' ','T'))
  $('#edit-species').val(row.data('species'))
  $('#edit-life_stage').val(row.data('life_stage'))
  $('#edit-sex').val(row.data('sex'))
  $('#edit-antler').val(row.data('antler'))
  $('#edit-animal_id').val(row.data('animal_id'))
  $('#edit-remarks').val(row.data('remarks'))
  $('#edit-image_uuid').val(row.data('image_uuid'))
  $('#edit-image_id').val(row.data('image_id'))
  $('#edit-image').html(row.find('td').last().html())

  if ($('#edit-image video').length) {
    $("#edit-image video").prop("controls", true);
  }

  if ($('#edit-image img').length) {
    $('#edit-image .img').attr('src', $('#edit-image .img').data('src')).addClass('w-100').addClass('h-auto');
  }

  $('#edit-image video source').on('error', function (event) {
    $(this).parent().parent().html('<p class="cannot-load" align="center">無法載入</p>')
  })
  $('#edit-image video source, #edit-image img').on('error', function (event) {
    $(this).parent().html('<p class="cannot-load" align="center">無法載入</p>')
  })


  let editable = window.editable;
  if ((editable != true) || ($('#edit_button').data('edit') == 'off')) {
    $('.edit-content input').attr('disabled', 'disabled')
    $('.edit-footer').addClass('d-none')
  } else {
    $('.edit-content input').prop("disabled", false)
    $('.edit-footer').removeClass('d-none')
  }


    // 上下張按鈕控制
    $('.photode-pop .arl, .photode-pop .arr').removeClass('d-none')
    $('.photode-pop .arr').unbind('click');
    $('.photode-pop .arr').on('click', function () {
      if (row.next('tr').length != 0) {
        changeEditContent(row.next('tr'));
      } else {
        updateTable($(`.page-inf .next`).data('page'), 'next')
      }
    })

    $('.photode-pop .arl').unbind('click');
    $('.photode-pop .arl').on('click', function () {
      if (row.prev('tr').length != 0) {
        changeEditContent(row.prev('tr'));
      } else {
        updateTable($(`.page-inf .back`).data('page'), 'back')
      }
    })

    $(document).off('keydown');
    $(document).on('keydown',function(e){
      if ($('#editModal.d-none').length == 0) {
        var arrow = { left: 37, right: 39 };
        switch (e.which) {
          case arrow.left:
            if (row.prev('tr').length != 0) {
              changeEditContent(row.prev('tr'));
            } else {
              updateTable($(`.page-inf .back`).data('page'), 'back')
            }
            break;
          case arrow.right:
            if (row.next('tr').length != 0) {
              changeEditContent(row.next('tr'));
            } else {
              updateTable($(`.page-inf .next`).data('page'), 'next')
            }
            break;
        }    
      }
    });


  // $('#editModal').off('keydown');
  // $('#editModal').keydown(function (e) {
  //   console.log(e)
  //   var arrow = { left: 37, right: 39 };
  //   switch (e.which) {
  //     case arrow.left:
  //       if (row.prev('tr').length != 0) {
  //         changeEditContent(row.prev('tr'));
  //       } else {
  //         updateTable($(`.page-inf .back`).data('page'), 'back')
  //         // $(`.page-inf .back`).trigger('click')
  //       }
  //       break;
  //     case arrow.right:
  //       if (row.next('tr').length != 0) {
  //         changeEditContent(row.next('tr'));
  //       } else {
  //         updateTable($(`.page-inf .next`).data('page'), 'next')
  //         // $(`.page-inf .next`).trigger('click')
  //       }
  //       break;
  //   }
  // });


}