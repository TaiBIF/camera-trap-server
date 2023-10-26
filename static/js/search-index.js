$(document).ready(function () {

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
  $("#download-email").keyup(function () {
    ValidateEmail($(this).val())
  });

  $('.down-pop .xx').on('click', function (event) {
  $('.down-pop').fadeOut();
  });
  $('#canceldownload').on('click', function (event) {
    $('.down-pop').fadeOut();
  });
});
