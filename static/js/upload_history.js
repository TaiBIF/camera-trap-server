$(document).ready(function() {

  // $('.setModal').on('click', function(){
  //   console.log($(this).data('deployment_journal_id'))
  //   let deployment_journal_id = $(this).data('deployment_journal_id');
  //   let species_error = $(this).data('species_error');
  //   let upload_error = $(this).data('upload_error');
  //     $('.error-link').attr("href", "/get_error_file_list/" + deployment_journal_id );
  //     species_error=='True' ? $('.species-error').show() : $('.species-error').hide()
  //     upload_error=='True' ? $('.upload-error').show() : $('.upload-error').hide()

  //   $('#errorModal').modal('show')

  // })
  
  $('.whybox').on('click',function (event) {
		$('.error-pop').removeClass('d-none');
		$('body').css("overflow", "hidden");
    let species_error = $(this).data('species_error');
    let upload_error = $(this).data('upload_error');
    species_error == 'True' ? $('.species-error').show() : $('.species-error').hide()
    species_error == 'True' ? $('.species-error-icon').show() : $('.species-error-icon').hide()
    upload_error == 'True' ? $('.upload-error').show() : $('.upload-error').hide()
    upload_error == 'True' ? $('.upload-error-icon').show() : $('.upload-error-icon').hide()
	});

  $('.xx').on('click',function (event) {
		$('.pop-box').addClass('d-none');
		$('body').css("overflow", "initial");
	});
})
