$( function() {

    $( ".datepicker" ).datepicker({
        dateFormat: "yy-mm-dd",
        });
    $( ".datepicker_publish" ).datepicker({
        dateFormat: "yy-mm-dd",
        defaultDate: "+5y",
        });

    // preselect region

    // let pk = $('input[name=pk]').val();
    // $.ajax({
    //   type: 'GET',
    //   url: `/api/get_edit_info/?pk=${pk}&type=basic`,
    //   success: function (response) {
    //     $('.selectpicker').selectpicker('val', response.region);
    // },
    // })



    $('#goBack').on('click',function(){
        window.history.back();
      })
  // validation

  $('#submitForm').on('click',function(){
      // name
      let name = $('[name="name"]')
      if (name.val()==''){
       name.addClass("is-invalid").addClass("was-validated");
      } else {
        name.removeClass("is-invalid").removeClass("was-validated").removeAttr("id", "invalid");
      }

      // principal_investigator
      let pi = $('[name="principal_investigator"]')
        if (pi.val()==''){
            pi.addClass("is-invalid").addClass("was-validated");
        } else {
            pi.removeClass("is-invalid").removeClass("was-validated").removeAttr("id", "invalid");
        }

      // start_date
      let start_date = $('[name="start_date"]');
        if (start_date.val()==''){
            start_date.addClass("is-invalid").addClass("was-validated");
        } else {
            try {
                date = $.datepicker.parseDate('yy-mm-dd', start_date.val());
                start_date.removeClass("is-invalid").removeClass("was-validated").removeAttr("id", "invalid");
            } catch (error) {
                start_date.addClass("is-invalid").addClass("was-validated");
        }
        }

      // end_date
      let end_date = $('[name="end_date"]');

        if (end_date.val()==''){
            end_date.addClass("is-invalid").addClass("was-validated");
        } else {
            try {
                date = $.datepicker.parseDate('yy-mm-dd', end_date.val());
                end_date.removeClass("is-invalid").removeClass("was-validated").removeAttr("id", "invalid");
            } catch (error) {
                end_date.addClass("is-invalid").addClass("was-validated");
            }
        }

    if(!$('.is-invalid').length){
        $('#editProjectBasic').submit()
    } else {
        $('.is-invalid').first().attr('id', 'invalid');
        window.location.href = "#invalid"
        window.location.hash = "#invalid"
    }

  })
  
  });

$(document).ready(function () {

    // select2
    let pk_test = $('input[name=pk]').val();
    $.ajax({
    type: 'GET',
    url: `/api/get_edit_info/?pk=${pk_test}&type=basic`,
    success: function (response) {
        $('#select-area').select2();
        $('#select-area').val(response.region).trigger('change');
    },
    });

    // Attach datepicker to calendar icon
    $('.date-start').click(function() {
        $('.datepicker-start').datepicker('show');
    });

    $('.date-end').click(function() {
        $('.datepicker-end').datepicker('show');
    });
    
    // Link pages
    $('.management-box .left-menu-area li:not(.now)').on('click', function(){
        location.href = $(this).data('href')
    });

});







