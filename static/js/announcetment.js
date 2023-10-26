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
      success: function(data, status) {
        $('.loading-pop').addClass('d-none');
        alert('請求已送出');
        window.f_data = new FormData();
      },
      error: function(xhr, desc, err) {
        $('.loading-pop').addClass('d-none');
        alert('未知錯誤，請聯繫管理員');
        window.f_data = new FormData();
      }
  });
});

$(document).ready(function() {
  $('.submit').on('click', function() {
      // clear previous validation
      $('.is-invalid').removeClass("is-invalid")
      let checked = true
      if ($('input[name=announcement-title]').val() == ''  || $('textarea[name=description]').val() == '') {
        checked = false
        $('.info-pop').removeClass('d-none');
        $('body').css("overflow", "hidden");

        if ($('input[name=announcement-title]').val() == '') {
            $('input[name=announcement-title]').addClass("is-invalid");
            $('.title-error').show();
            $('.title-error-icon').show();
        } else {
            $('.title-error').hide();
            $('.title-error-icon').hide();
        };

        if ($('textarea[name=description]').val() == '') {
            $('textarea[name=description]').addClass("is-invalid");
            $('.content-error').show();
            $('.content-error-icon').show();
        } else {
            $('.content-error').hide();
            $('.content-error-icon').hide();
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

  window.file_list = {}
  window.file_index = 0
  window.f_data = new FormData()
  window.f_total_size = 0
});
