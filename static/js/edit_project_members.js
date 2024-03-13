$(".select-sa").select2({placeholder: "請選擇", language: "zh-TW"});


$( function() {

    $('.management-box .left-menu-area li:not(.now)').on('click', function(){
      location.href = $(this).data('href')
    })

    $('#goBack').on('click',function(){
        window.history.back();
      })
  
      $('#submitAddForm').on('click', function(event){
        // $('#addProjectMember').submit()
        event.preventDefault();

        var csrftoken = $("[name=csrfmiddlewaretoken]").val();

        const data = {
          'contact_query': $('div.input-item input[name="contact_query"]').val(),
          'role': $('div.input-item select[name="role"]').val(),
          'action': 'add'
        }

        $.ajax({
            type: 'POST',
            url: $('#addProjectMember').attr('action'),
            headers: {
              'X-CSRFToken': csrftoken
            },
            data: data,
            success: function (response) {
              if (response.return_message == '新增成功') {
                $('.add-success-pop').removeClass('d-none')
              } else {
                $('.add-fail-pop').removeClass('d-none')
              }
            },
            error: function (xhr, status, error) {
              $('.add-fail-pop').removeClass('d-none')
            }
        });
      })

      $('.check-pop').on('click', function() {
        $('.add-success-pop').addClass('d-none')
        location.reload();
      })

      $('#submitEditForm').on('click',function(){
        $('#editProjectMember').submit()
      })

      $('#removePM').on('click',function(){
        $('#removeProjectMember').submit()
      })

      $('.remove').on('click', function(){
        var memberid = $(this).data('id');
        $(".remove-pop #memberid").val( memberid );
        $(".remove-pop #remove_mame").html( $(this).data('name') );
        $('.remove-pop').removeClass('d-none')   
      })


      $('.calcel-remove').on('click', function(){
        $('.remove-pop').addClass('d-none')   
      })

      // if ($('input[name=return_message]').val()!=''){
      //   alert($('input[name=return_message]').val())
      // }

})
