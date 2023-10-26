$(document).ready(function () {
    // Switch checkbox: metadata-select-box
    const metadata_checkboxes = document.querySelectorAll('.metadata-select-box .item .cir-checkbox');
     metadata_checkboxes.forEach(checkbox => {
      checkbox.addEventListener('click', function() {
        console.log('Checkbox clicked')
        const metadata_itemsWithNowClass = document.querySelectorAll('.metadata-select-box .item.now');
        metadata_itemsWithNowClass.forEach(item => {
          item.classList.remove('now');
        });

        const metadata_listItem = this.closest('.item');
        metadata_listItem.classList.add('now');
      });
    });

    // Switch checkbox: identification-select-box
    const identification_checkboxes = document.querySelectorAll('.identification-select-box .item .cir-checkbox');
    identification_checkboxes.forEach(checkbox => {
      checkbox.addEventListener('click', function() {
        console.log('Checkbox clicked')
        const identification_itemsWithNowClass = document.querySelectorAll('.identification-select-box .item.now');
        identification_itemsWithNowClass.forEach(item => {
          item.classList.remove('now');
        });

        const identification_listItem = this.closest('.item');
        identification_listItem.classList.add('now');
      });
    });

    // Switch checkbox: image-select-box
    const image_checkboxes = document.querySelectorAll('.image-select-box .item .cir-checkbox');
    image_checkboxes.forEach(checkbox => {
      checkbox.addEventListener('click', function() {
        console.log('Checkbox clicked')
        const image_itemsWithNowClass = document.querySelectorAll('.image-select-box .item.now');
        image_itemsWithNowClass.forEach(item => {
            item.classList.remove('now');
        });

        const image_listItem = this.closest('.item');
        image_listItem.classList.add('now');
      });
    });

    // Attach datepicker to calendar icon
    $('.date-publish').click(function() {
        $('.datepicker_publish').datepicker('show');
    });

    // Link pages
    $('.management-box .left-menu-area li:not(.now)').on('click', function(){
      location.href = $(this).data('href')
    });

    $(".datepicker_publish").datepicker({
      dateFormat: "yy-mm-dd",
      defaultDate: "+5y",
    });

    // precheck license
    let pk = $('input[name=pk]').val();
    $.ajax({
      type: 'GET',
      url: `/api/get_edit_info/?pk=${pk}&type=license`,
      success: function (response) {
        $(`[name="interpretive_data_license"][value="${ response.interpretive_data_license }"]`).attr("checked", "checked");
        $(`[name="identification_information_license"][value="${ response.identification_information_license }"]`).attr("checked", "checked");
        $(`[name="video_material_license"][value="${ response.video_material_license }"]`).attr("checked", "checked");

        // Check if atrribute checked exists
        const metadata_itemDivs = document.querySelectorAll('.metadata-select-box .item');
        metadata_itemDivs.forEach(itemDiv => {
            const inputElement = itemDiv.querySelector('input[name="interpretive_data_license"]');

            if (inputElement && inputElement.getAttribute('checked') === 'checked') {
                itemDiv.classList.add('now');
            }
        });

        const identification_itemDivs = document.querySelectorAll('.identification-select-box .item');
        identification_itemDivs.forEach(itemDiv => {
            const inputElement = itemDiv.querySelector('input[name="identification_information_license"]');

            if (inputElement && inputElement.getAttribute('checked') === 'checked') {
                itemDiv.classList.add('now');
            }
        });

        const image_itemDivs = document.querySelectorAll('.image-select-box .item');
        image_itemDivs.forEach(itemDiv => {
            const inputElement = itemDiv.querySelector('input[name="video_material_license"]');

            if (inputElement && inputElement.getAttribute('checked') === 'checked') {
                itemDiv.classList.add('now');
            }
        });
      }
  
    });
 
 
    $('#goBack').on('click',function(){
      window.history.back();
    })
  

  // validation
  $('#submitForm').on('click', function(){
    // publish_date
    let publish_date = $('[name="publish_date"]');

    if (publish_date.val() == "") {
      publish_date.addClass("is-invalid").addClass("was-validated");
    } else {
      try {
        date = $.datepicker.parseDate("yy-mm-dd", publish_date.val());
        publish_date.removeClass("is-invalid").removeClass("was-validated").removeAttr("id", "invalid");
      } catch (error) {
        publish_date.addClass("is-invalid").addClass("was-validated");
      }
    }

    if (!$(".is-invalid").length) {
      $("#editProjectLicense").submit();
    } else {
      $(".is-invalid").first().attr("id", "invalid");
      window.location.href = "#invalid";
      window.location.hash = "#invalid";
    }

  })


  });
