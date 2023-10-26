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


    $(".datepicker").datepicker({
        dateFormat: "yy-mm-dd",
    });

    // Attach datepicker to calendar icon
    $('.date-start').click(function() {
        $('.datepicker-start').datepicker('show');
    });

    $('.date-end').click(function() {
        $('.datepicker-end').datepicker('show');
    });

    $('.date-publish').click(function() {
        $('.datepicker_publish').datepicker('show');
    });

    $(".datepicker_publish").datepicker({
        dateFormat: "yy-mm-dd",
        defaultDate: "+5y",
      });

    // select2
    $('#select-area option:selected').val();
    $("#select-area").select2({});
    $("#select-area").val(null).trigger('change');
    
    // Close pop-box
    $('.xx').on('click',function (event) {
      $('.pop-box').addClass('d-none');
      $('body').css("overflow", "initial");
    });
});


  $('#validateForm').on('click',function(){

    let name = $('[name="name"]');
    let pi = $('[name="principal_investigator"]');

    if (name.val() == "" || pi.val() == "") {

      if (name.val() == "") {
        name.addClass("is-invalid").addClass("was-validated");
        $('.input-pop-3').removeClass('d-none');
        $('body').css("overflow", "hidden");
        $('.name-error').show();
        $('.name-error-icon').show();
      } else {
        name.removeClass("is-invalid").removeClass("was-validated").removeAttr("id", "invalid");
        $('.name-error').hide();
        $('.name-error-icon').hide();
      };

      if (pi.val() == "") {
        pi.addClass("is-invalid").addClass("was-validated");
        $('.input-pop-3').removeClass('d-none');
        $('body').css("overflow", "hidden");
        $('.principal-error').show();
        $('.principal-error-icon').show();
      } else {
        pi.removeClass("is-invalid").removeClass("was-validated").removeAttr("id", "invalid");
        $('.principal-error').hide();
        $('.principal-error-icon').hide();
      }
      
    } 
    // // name
    // let name = $('[name="name"]');
    // if (name.val() == "") {
    //   name.addClass("is-invalid").addClass("was-validated");
    //   $('.name-pop').removeClass('d-none');
    //   $('body').css("overflow", "hidden");
    // } else {
    //   name.removeClass("is-invalid").removeClass("was-validated").removeAttr("id", "invalid");
    // }

    // // principal_investigator
    // let pi = $('[name="principal_investigator"]');
    // if (pi.val() == "") {
    //   pi.addClass("is-invalid").addClass("was-validated");
    //   $('.principal-pop').removeClass('d-none');
    //   $('body').css("overflow", "hidden");
    // } else {
    //   pi.removeClass("is-invalid").removeClass("was-validated").removeAttr("id", "invalid");
    // }

    // start_date
    let start_date = $('[name="start_date"]');
    if (start_date.val() == "") {
      start_date.addClass("is-invalid").addClass("was-validated");
    } else {
      try {
        date = $.datepicker.parseDate("yy-mm-dd", start_date.val());
        start_date.removeClass("is-invalid").removeClass("was-validated").removeAttr("id", "invalid");
      } catch (error) {
        start_date.addClass("is-invalid").addClass("was-validated");
      }
    }

    // end_date
    let end_date = $('[name="end_date"]');

    if (end_date.val() == "") {
      end_date.addClass("is-invalid").addClass("was-validated");
    } else {
      try {
        date = $.datepicker.parseDate("yy-mm-dd", end_date.val());
        end_date.removeClass("is-invalid").removeClass("was-validated").removeAttr("id", "invalid");
      } catch (error) {
        end_date.addClass("is-invalid").addClass("was-validated");
      }
    }

    if (!$(".is-invalid").length) {
      $("#first-page").hide();
      $("#second-page").show();
      window.location.hash = "#second-page";
      window.location.href = "#second-page";
    } else {
      $(".is-invalid").first().attr("id", "invalid");
      window.location.href = "#invalid";
      window.location.hash = "#invalid";
    }

  })


  $('#submitForm').on('click', function(){
    // publish_date

    let check = [];
    let publish_date = $('[name="publish_date"]');

    if (publish_date.val() == "") {
      publish_date.addClass("is-invalid").addClass("was-validated");
      check.push(false);
    } else {
      try {
        date = $.datepicker.parseDate("yy-mm-dd", publish_date.val());
        publish_date.removeClass("is-invalid").removeClass("was-validated");
      } catch (error) {
        publish_date.addClass("is-invalid").addClass("was-validated");
        check.push(false);
      }
    }

    if (!$(".is-invalid").length) {
      $("#createProjectForm").submit();
    };

})

