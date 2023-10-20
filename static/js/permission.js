
$('#goBack').on('click',function(){
window.history.back();
})



$('#submitAddForm').on('click',function(){
    $('#addOrgAdmin').submit();
})


$('#addOrgProjectClick').on('click', function(){
    $('#addOrgProject').submit();
})

// if ($('input[name=return_message]').val()!=''){
//   alert($('input[name=return_message]').val())
// };


$(document).ready(function () {

    // pop-box
    $('.remove').on('click',function (event) {
        var id = $(this).data('id');
        var type = $(this).data('type');
        $(".modal-body #id").val( id );
        $(".modal-body #type").val( type );
        $('.error-pop').removeClass('d-none');
        $('body').css("overflow", "hidden");
        console.log(id);
        console.log(type);
    });

    $('#remove-click').on('click',function(){
        $('#removeBtn').submit()
    })

    $('.xx').on('click',function (event) {
        $('.error-pop').addClass('d-none');
        $('body').css("overflow", "initial");
    });

    // select2
    $('#select-member option:selected').val();
    $("#select-member").select2({});
    $("#select-member").val(null).trigger('change');

    $('#select-member-org option:selected').val();
    $("#select-member-org").select2({});
    $("#select-member-org").val(null).trigger('change');

    $('#select-project option:selected').val();
    $("#select-project").select2({});
    $("#select-project").val(null).trigger('change');

    $('#select-project-org option:selected').val();
    $("#select-project-org").select2({});
    $("#select-project-org").val(null).trigger('change');

});

