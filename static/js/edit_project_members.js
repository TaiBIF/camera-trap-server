$(".select-sa").select2({placeholder: "請選擇", language: "zh-TW"});


$( function() {

    $('.management-box .left-menu-area li:not(.now)').on('click', function(){
      location.href = $(this).data('href')
    })

    $('#goBack').on('click',function(){
        window.history.back();
      })
  
      $('#submitAddForm').on('click', function(){
        $('#addProjectMember').submit()
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

      if ($('input[name=return_message]').val()!=''){
        alert($('input[name=return_message]').val())
      }

})
