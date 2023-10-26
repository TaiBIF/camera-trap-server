$(document).ready(function() {
  // Upload files
  $('#f-upload').change(function() {
    let f;
    for (let i = 0; i < this.files.length; i++) {
      window.file_index += 1;
      f = this.files[i];
      if ((window.f_total_size + f.size) / (1024 * 1024) > 20) {
        $("#f-list").append(`<li class="d-flex align-items-center mb-2"><p class="f-label">${f.name}</p> <span class="notice ms-2">檔案過大，已移除 </span></li>`);
      } else if (f.size / (1024 * 1024) > 20) {
        $("#f-list").append(`<li class="d-flex align-items-center mb-2"><p class="f-label">${f.name}</p> <span class="notice ms-2">檔案過大，已移除 </span></li>`);
      } else {
        $("#f-list").append(`<li class="d-flex align-items-center mb-2">
          <p class="f-label">${f.name}</p>
          <button class="delete-file-btn" data-index="${window.file_index}">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 18.828 18.828">
              <g data-name="Group 688" transform="translate(-1823.086 -445.086)">
                <line data-name="Line 1" x1="16" y2="16" transform="translate(1824.5 446.5)" fill="none" stroke="#257455" stroke-linecap="round" stroke-width="2"/>
                <line data-name="Line 2" x2="16" y2="16" transform="translate(1824.5 446.5)" fill="none" stroke="#257455" stroke-linecap="round" stroke-width="2"/>
              </g>
            </svg>
          </button>
        </li>`);
        var file = this.files[i];
        window.file_list[window.file_index] = { 'file': file };
        window.f_data.append("uploaded_file", file, file.name);
        window.f_total_size += f.size;
      }
    }
    $('.delete-file-btn').on('click', function() {
      const dataIndex = $(this).data('index');
      delete window.file_list[dataIndex];
      // Delete from FormData
      window.f_data.delete('uploaded_file');
      window.f_total_size = 0;
      // Re-append to FormData
      Object.entries(window.file_list).forEach(([k, v]) => {
        window.f_data.append("uploaded_file", v['file'], v['file'].name);
        window.f_total_size += v['file'].size;
      })
      console.log(window.f_total_size)
      $(this).parent().remove();
    });
  });

  // Switch checkbox
  const checkboxes = document.querySelectorAll('.check-list li');
  checkboxes.forEach(checkbox => {
    checkbox.addEventListener('click', function() {
      console.log('Checkbox clicked')
      const itemsWithNowClass = document.querySelectorAll('.check-list li.now');
      itemsWithNowClass.forEach(item => {
        item.classList.remove('now');
      });

      const listItem = this.closest('li');
      listItem.classList.add('now');
    });
  });

  // Submit the question
  $(document).on("submit", "form", function(event) {
    $('.loading-pop').removeClass('d-none');
    event.preventDefault();
    
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
        $('.loading-pop').addClass('d-none');
        alert('請求已送出');
        window.f_data = new FormData();
      },
      error: function (xhr, desc, err) {
        $('.loading-pop').addClass('d-none');
        alert('未知錯誤，請聯繫管理員');
        window.f_data = new FormData();
      }
    });
  });

  // Validate input
  $('.submit').on('click', function() {
    console.log('submit clicked')
    
    $('.is-invalid').removeClass("is-invalid")
    let checked = true

    if (!ValidateEmail($("input[name=email]").val()) || $('textarea[name=description]').val() == '') {
        checked = false
        $('.info-pop-2').removeClass('d-none');
        $('body').css("overflow", "hidden");

        if ($('input[name=email]').val() == '') {
          $('input[name=email]').addClass("is-invalid");
          $('.mail-error').show();
          $('.mail-error-icon').show();
      } else {
          $('.title-error').hide();
          $('.title-error-icon').hide();
      };

      if ($('textarea[name=description]').val() == '') {
          $('textarea[name=description]').addClass("is-invalid");
          $('.description-error').show();
          $('.description-error-icon').show();
      } else {
          $('.description-error').hide();
          $('.description-error-icon').hide();
      };
    };
    
    
    if (checked) {
      $('#submitForm').submit()
    };

    $('.xx').on('click',function (event) {
      $('.pop-box').addClass('d-none');
      $('body').css("overflow", "initial");
    });
  });

  function ValidateEmail(inputText) {
    let mailformat = /(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])/;
    if (inputText.match(mailformat)) {
      return true;
    } else {
      return false;
    }
  }
});
