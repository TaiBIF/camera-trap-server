var $csrf_token = $('[name="csrfmiddlewaretoken"]').attr('value');
let pk = $('input[name=pk]').val();

$( function() {

    $('.management-box .left-menu-area li:not(.now)').on('click', function(){
        location.href = $(this).data('href')
    })

    $('select[name=sa-select]').on('change', function(){
        if ($('select[name=sa-select]').val()){
            $('.area-table').removeClass('d-none')
            // 整理表格
            $('#selected-sa-name').html($('select[name=sa-select]:selected').data('saname'))
            getDep($('select[name=sa-select]').val(), $( "select[name=sa-select] option:selected" ).text())
        } else {
            $('.area-table').addClass('d-none')
        }

    })


    $('#goBack').on('click',function(){
        window.history.back();
    })


    // 新增樣區
    $('.add-newbtn').on('click',function (event) {
        // 清空pop的內容
        $('#addStudyArea-feedback').html('')
        $('#addStudyArea').val('')
		$('.addare-pop').removeClass('d-none');
	});
        
    $('#addSa').on('click',function(){
        let name = $('#addStudyArea').val();
        name_list = []
        $('select[name=sa-select] option').each(function(){
            name_list.push($(this).text());
        });
        if (name=='' ){
            $('#addStudyArea-feedback').html('*樣區名稱為必填');
        } else if (name_list.includes(name)){
            $('#addStudyArea-feedback').html('*樣區名稱不得重複');
        } else {
            $.ajax({
                type: 'POST',
                url: "/api/add_studyarea",
                data: {'name': name, 'project_id': $('input[name=pk]').val()},
                headers:{"X-CSRFToken": $csrf_token},
                success: function (response) {
                    let new_id = response.study_area_id;
                    $('select[name=sa-select]').append(
                        `<option value="${ new_id }" id="${ new_id }" data-said="${ new_id }" data-saname="${ name }">${ name }</option>`
                    )
                    $('select[name=sa-select]').val(new_id).change();
                    $('.addare-pop').addClass('d-none')

                },
                error: function (response) {
                    $('.addare-pop').addClass('d-none')
                    alert('未知錯誤，請聯繫管理員')
                }
            })
        }
    
    })

    // 編輯樣區

    $('.edit-btn').on('click',function (event) {
        $('#editStudyArea').val($('#selected-sa-name').html());
        $('#editStudyArea-id').val($('select[name=sa-select]').val());
        // 清空先前的內容
        $('#editStudyArea-feedback').html('')
		$('.editare-pop').removeClass('d-none');
	});

    
    $('#editSa_edit').on('click',function(){
        let name = $('#editStudyArea').val();
        // 也有可能是sub
        let original_name = $('#selected-sa-name').html();
        name_list = []
        $('select[name=sa-select] option').each(function(){
            if ($(this).text() != original_name){
                name_list.push($(this).text());
            }
        });

        if (name=='' ){
            $('#editStudyArea-feedback').html('*樣區名稱為必填');
        } else if (name_list.includes(name)){
            $('#editStudyArea-feedback').html('*樣區名稱不得重複');
        } else {
            
            $.ajax({
                type: 'GET',
                url: "/edit_sa",
                data: {'name': name, 'id': $('#editStudyArea-id').val()},
                success: function (response) {
                    // 修改下方列表名稱
                    $('#selected-sa-name').html(name)
                    // 修改select option名稱
                    $('select[name=sa-select]').find("option:selected").text(name);
                    $('.editare-pop').addClass('d-none');
                    alert('設定已儲存')
                },
                error: function (response) {
                    alert('未知錯誤，請聯繫管理員')
                }
            })
            
        }    
    })

    // 刪除樣區

    $('#editSa_delete').on('click',function(){
        $.ajax({
            type: 'GET',
            url: "/delete_dep_sa",
            data: {'type': 'sa', 'id': $('#editStudyArea-id').val(), 'project_id': $('input[name=pk]').val()},
            success: function (response) {
                if (response.status=='exists'){
                    alert('欲刪除的樣區下尚有影像，請先刪除影像或將影像搬移至其他樣區')
                } else if (response.status=='done') {
                    alert('已成功刪除')
                    location.reload()
                }
            },
            error: function (response) {
                alert('未知錯誤，請聯繫管理員');
            }
        })
    })


    // 儲存相機位置設定
    $('#addDepolymentSubmit').on('click',function(){
        // check required fields
        // name
        let name = $('#deployment [name="name"]')

        name_list = []
        name.each(function(){
            name_list.push($(this).val());
        });

        name.each(function(){
            if ($(this).val()==''){
                $(this).addClass("is-invalid")
            } else if (name_list.includes($(this).val())){
                let count = 0;
                for(let i = 0; i < name_list.length; ++i){
                    if(name_list[i] == $(this).val())
                        count++;
                }
                if (count > 1){
                    $(this).addClass("is-invalid")
                } else {
                    $(this).removeClass("is-invalid")
                }
            } else {
                $(this).removeClass("is-invalid")
            }            
        });

        let longitude = $('#deployment [name="longitude"]')
        longitude.each(function(){
            let value = $(this).val()
            if (!$.isNumeric(value)){
                $(this).addClass("is-invalid")
            } else {
                $(this).removeClass("is-invalid")
            }            
        });

        let latitude = $('#deployment [name="latitude"]')
        latitude.each(function(){
            let value = $(this).val()
            if (!$.isNumeric(value)){
                $(this).addClass("is-invalid")
            } else {
                $(this).removeClass("is-invalid")
            }            
        });

        // altitude
        let altitude = $('#deployment [name="altitude"]')
        altitude.each(function(){  
            let value = $(this).val()
            if (value==''){
                //pass
            } else {
                if (!$.isNumeric(value)){
                    $(this).addClass("is-invalid")
                } else {
                    $(this).removeClass("is-invalid")
                }
            }
        });

        // submit
        if(!$('#deployment .is-invalid').length){

            names = []
            name.each(function(){
                names.push($(this).val());
            });

            latitudes = []
            latitude.each(function(){
                latitudes.push($(this).val());
            });

            longitudes = []
            longitude.each(function(){
                longitudes.push($(this).val());
            });

            altitudes = []
            altitude.each(function(){
                altitudes.push($(this).val());
            });

            counties = []
            $('#deployment [name="county"]').each(function(){
                counties.push($(this).val());
            });
            protectedareas = []
            $('#deployment [name="protectedarea"]').each(function(){
                protectedareas.push($(this).val().toString());
            });

            landcovers = []
            $('#deployment [name="landcover"]').each(function(){
                landcovers.push($(this).val());
            });

            vegetations = []
            $('#deployment [name="vegetation"]').each(function(){
                vegetations.push($(this).val());
            });

            did = []
            $('#deployment [name="id"]').each(function(){
                did.push($(this).val());
            });

            deprecated = []
            $('input[name="deprecated"]:checked').each(function(){
                deprecated.push($(this).val());
            });
            
            $.ajax({
            type: 'POST',
            url: "/api/add_deployment",
            data: {'project_id': $('input[name=pk]').val(),
                'study_area_id': $('.current_sa').attr('id'),
                'geodetic_datum': $('#geodetic_datum').val(),
                'names': names,
                'longitudes': longitudes,
                'latitudes': latitudes,
                'altitudes': altitudes,
                'counties': counties,
                'protectedareas': protectedareas,
                'landcovers' : landcovers,
                'vegetations': vegetations,
                'did': did,
                'deprecated': deprecated},
            headers:{"X-CSRFToken": $csrf_token},
            success: async function (response) {
                // 如果有新增的話，要把新增的deployment_id寫回去
                // 改成remove沒有did的 然後新增回去
                $('.new-row').remove();
                
                var vegetation = await getVegetationItem().then(result => vegetation = result)
            
                var protectedarea = await getProtectedareaItem().then(result => protectedarea = result)
                
                var county = await getCountyItem().then(result => county = result)

                for (let i = 0; i < response.length; i++) {
                    // 如果是null顯示空值
                    for (j = 0; j < 9; j++ ){
                        if ((response[i][j] == null)|(response[i][j] == 'null')){
                            response[i][j] = ""}
                    }

                    let d_checked
                    if (response[i][11]==true){
                        d_checked='checked';
                    }

                    let protectedarea_a = [];
                        for (let j = 0; j < protectedarea.length; j++) {
                            if (response[i][6]){
                                a = protectedarea[j].toString().replace(response[i][6], response[i][6]+' selected')
                                protectedarea_a.push(a)
                            }else{
                                protectedarea_a.push(protectedarea[j].toString())
                            }
                        }
                        
                    let vegetation_a = [];
                    for (let j = 0; j < vegetation.length; j++) {
                        if (response[i][7]){
                            a = vegetation[j].toString().replace(response[i][7], response[i][7]+' selected')
                            vegetation_a.push(a)
                        }else{
                            vegetation_a.push(vegetation[j].toString())
                        }
                    }
                    
                    let county_a = [];
                    for (let j = 0; j < county.length; j++) {
                        if (response[i][5]){
                            a = county[j].toString().replace(response[i][5], response[i][5]+' selected')
                            county_a.push(a)
                        }else{
                            county_a.push(county[j].toString())
                        }
                    }

                    await $('#deployment').append(`
                        <tr>
                            <td>
                                <input type="hidden" name="id" value="${response[i][0]}">
                                <div class="input-item">
                                    <input type="text" name="name" value="${response[i][1]}">
                                </div>
                            </td>
                            <td>
                                <div class="input-item">
                                <input type="text" name="longitude" value="${response[i][2]}">
                                </div>
                            </td>
                            <td>
                                <div class="input-item">
                                <input type="text" name="latitude" value="${response[i][3]}">
                                </div>
                            </td>
                            <td>                        
                                <div class="input-item">
                                <input type="text" name="altitude" value="${response[i][4]}">
                                </div>
                            </td>
                            <td>
                                <div class="input-item">
                                <select name="county" class="">${county_a}</select>
                                </div>
                            </td>
                            <td>
                                <div class="input-item">
                                <select name="protectedarea" class="" multiple="multiple">${protectedarea_a}</select>
                                </div>
                            </td>
                            <td>
                                <div class="input-item">
                                <select name="vegetation" class="">${vegetation_a}</select>
                                </div>
                            </td>
                            <td>
                                <div class="input-item">
                                <input type="text" name="landcover" value="${response[i][8]}">
                                </div>
                            </td>
                            <td>
                                <input class="checkbox" type="checkbox" name="deprecated" value="${i}" ${d_checked}>
                            </td>
                            <td>
                                <a class="removeButton" data-did="${response[i][0]}">
                                <svg xmlns="http://www.w3.org/2000/svg" width="20.828" height="20.828" viewBox="0 0 20.828 20.828">
                                    <g data-name="Group 689" transform="translate(-1823.086 -445.086)">
                                        <line data-name="Line 1" x1="18" y2="18" transform="translate(1824.5 446.5)" fill="none" stroke="#cb5757" stroke-linecap="round" stroke-width="2"/>
                                        <line data-name="Line 2" x2="18" y2="18" transform="translate(1824.5 446.5)" fill="none" stroke="#cb5757" stroke-linecap="round" stroke-width="2"/>
                                    </g>
                                </svg>
                                </a>
                            </td>
                        </tr>`)
                }

                $('select[name=protectedarea]').select2({placeholder:'--請選擇--',language: "zh-TW"})
                $('select[name=vegetation]').select2({language: "zh-TW"})
                $('select[name=county]').select2({language: "zh-TW"})    
            
                alert('設定已儲存');
            },
            error: function (response) {
                alert('未知錯誤，請聯繫管理員');
            }
        })
        
        } else {
            alert('請檢查輸入欄位是否正確，且相機位置名稱不得重複');
        }

    })

    // 新增相機位置

    $('#addDeployment').on('click',async function(){
        var vegetation = await getVegetationItem().then(result => vegetation = result)
        var protectedarea = await getProtectedareaItem().then(result => protectedarea = result)
        var county = await getCountyItem().then(result => county = result)
        
        //目前的id到哪
        let new_id = parseInt($('input[name=deprecated]').last().val()) + 1;

        $('#deployment').append(`
        <tr class="new-row">
            <td>
                <input type="hidden" name="id" value="">
                <div class="input-item">
                    <input type="text" name="name" value="">
                </div>
            </td>
            <td>
                <div class="input-item">
                <input type="text" name="longitude" value="">
                </div>
            </td>
            <td>
                <div class="input-item">
                <input type="text" name="latitude" value="">
                </div>
            </td>
            <td>                        
                <div class="input-item">
                <input type="text" name="altitude" value="">
                </div>
            </td>
            <td>
                <div class="input-item">
                <select name="county" class="">${county}</select>
                </div>
            </td>
            <td>
                <div class="input-item">
                <select name="protectedarea" class="" multiple="multiple">${protectedarea}</select>
                </div>
            </td>
            <td>
                <div class="input-item">
                <select name="vegetation" class="">${vegetation}</select>
                </div>
            </td>
            <td>
                <div class="input-item">
                <input type="text" name="landcover" value="">
                </div>
            </td>
            <td>
                <input class="checkbox" type="checkbox" name="deprecated" value="${new_id}">
            </td>
            <td>
                <a class="removeButton" data-did="">
                <svg xmlns="http://www.w3.org/2000/svg" width="20.828" height="20.828" viewBox="0 0 20.828 20.828">
                    <g data-name="Group 689" transform="translate(-1823.086 -445.086)">
                        <line data-name="Line 1" x1="18" y2="18" transform="translate(1824.5 446.5)" fill="none" stroke="#cb5757" stroke-linecap="round" stroke-width="2"/>
                        <line data-name="Line 2" x2="18" y2="18" transform="translate(1824.5 446.5)" fill="none" stroke="#cb5757" stroke-linecap="round" stroke-width="2"/>
                    </g>
                </svg>
                </a>
            </td>
        </tr>`)

        $('select[name=protectedarea]').select2({placeholder:'--請選擇--',language: "zh-TW"})
        $('select[name=vegetation]').select2({language: "zh-TW"})
        $('select[name=county]').select2({language: "zh-TW"})

    })

})



function getVegetationItem(){
    return new Promise((resolve, reject) => {
        obj2 = []
        $.ajax({
            type: 'GET',
            url: "/api/get_parameter_name/",
            data: {'type': 'vegetation'},
            headers:{"X-CSRFToken": $csrf_token},
            async:false,
            success: function (data) {
                obj2.push(`<option value="none" selected>--請選擇--</option>`)
                for (let i = 0; i < data.length; i++) {
                    obj2.push(`<option value=${data[i]['parametername']}>${data[i]['name']}</option>`)
                }
                resolve (obj2)
            },
            error: function (response) {
                reject(Error('something wrong!'));
            }
        })   
    })
}

function getCountyItem(){
    return new Promise((resolve, reject) => {
        obj4 = []
        $.ajax({
            type: 'GET',
            url: "/api/get_parameter_name/",
            data: {'type': 'county'},
            headers:{"X-CSRFToken": $csrf_token},
            async:false,
            success: function (data) {
                obj4.push(`<option value='none' selected>--請選擇--</option>`)
                for (let i = 0; i < data.length; i++) {
                    obj4.push(`<option value=${data[i]['parametername']}>${data[i]['name']}</option>`)
                }
                resolve (obj4)
            },
            error: function (response) {
                reject(Error('something wrong!'));
            }
        })   
    })
}

function getProtectedareaItem(){
    return new Promise((resolve, reject) => {
        obj3 = []
        $.ajax({
            type: 'GET',
            url: "/api/get_parameter_name/",
            data: {'type': 'protectedarea'},
            headers:{"X-CSRFToken": $csrf_token},
            async:false,
            success: function (data) {
                for (let i = 0; i < data.length; i++) {
                    obj3.push(`<option value=${data[i]['parametername']}>${data[i]['name']}</option>`)
                }
                resolve(obj3)
            },
            error: function (response) {
                reject(Error('something wrong!'));
            }
        })   
    })
}


function getDep(id, sa_name){
    // clear previous select
    $('#deployment').html('')
    $('#selected-sa-name').html(sa_name);

    let selector = '#' + id
    $(selector).addClass("title-dark").addClass('current_sa')

    //判斷選項
    vegetation = []
    var vegetation =  getVegetationItem().then(result => vegetation = result)

    protectedarea = []
    var protectedarea =  getProtectedareaItem().then(result => protectedarea = result)

    county = []
    var county =  getCountyItem().then(result => county = result)
    
    // deployment    
    $.ajax({
        type: 'POST',
        url: "/api/deployment/",
        data: {'study_area_id': id},
        headers:{"X-CSRFToken": $csrf_token},
        success: function (response) {
            //let data = JSON.parse(response.replace(/'/g, '"'))
            for (let i = 0; i < response.length; i++) {
                // 如果是null顯示空值
                for (j = 0; j < 7; j++ ){
                    if ((response[i][j] == null)|(response[i][j] == 'null')){
                        response[i][j] = ""}
                }
                let d_checked
                if (response[i][11]==true){
                    d_checked='checked';
                }

                let protectedarea_a = protectedarea.slice();
                for (let j = 0; j < protectedarea_a.length; j++) {
                    res_item = response[i][6].split(',')
                    for  (let k = 0; k < res_item.length; k++) {
                        if (protectedarea_a[j].toString().search(res_item[k].toString())){
                            protectedarea_a[j] = protectedarea_a[j].toString().replace(res_item[k], res_item[k]+' selected')
                        }
                    }
                }
                
                let vegetation_a = [];

                for (let j = 0; j < vegetation.length; j++) {
                    if (response[i][7]){
                        a = vegetation[j].toString().replace(response[i][7], response[i][7]+' selected')
                        vegetation_a.push(a)
                    }else{
                        vegetation_a.push(vegetation[j].toString())
                    }
                }

                let county_a = [];
                for (let j = 0; j < county.length; j++) {
                    if (response[i][5]){
                        a = county[j].toString().replace(response[i][5], response[i][5]+' selected')
                        county_a.push(a)
                    }else{
                        county_a.push(county[j].toString())
                    }
                }
                $('#deployment').append(`
                <tr>
                    <td>
                        <input type="hidden" name="id" value="${response[i][0]}">
                        <div class="input-item">
                            <input type="text" name="name" value="${response[i][1]}">
                        </div>
                    </td>
                    <td>
                        <div class="input-item">
                        <input type="text" name="longitude" value="${response[i][2]}">
                        </div>
                    </td>
                    <td>
                        <div class="input-item">
                        <input type="text" name="latitude" value="${response[i][3]}">
                        </div>
                    </td>
                    <td>                        
                        <div class="input-item">
                        <input type="text" name="altitude" value="${response[i][4]}">
                        </div>
                    </td>
                    <td>
                        <div class="input-item">
                        <select name="county" class="">${county_a}</select>
                        </div>
                    </td>
                    <td>
                        <div class="input-item">
                        <select name="protectedarea" class="" multiple="multiple">${protectedarea_a}</select>
                        </div>
                    </td>
                    <td>
                        <div class="input-item">
                        <select name="vegetation" class="">${vegetation_a}</select>
                        </div>
                    </td>
                    <td>
                        <div class="input-item">
                        <input type="text" name="landcover" value="${response[i][8]}">
                        </div>
                    </td>
                    <td>
                        <input class="checkbox" type="checkbox" name="deprecated" value="${i}" ${d_checked}>
                    </td>
                    <td>
                        <a class="removeButton" data-did="${response[i][0]}">
                        <svg xmlns="http://www.w3.org/2000/svg" width="20.828" height="20.828" viewBox="0 0 20.828 20.828">
                            <g data-name="Group 689" transform="translate(-1823.086 -445.086)">
                                <line data-name="Line 1" x1="18" y2="18" transform="translate(1824.5 446.5)" fill="none" stroke="#cb5757" stroke-linecap="round" stroke-width="2"/>
                                <line data-name="Line 2" x2="18" y2="18" transform="translate(1824.5 446.5)" fill="none" stroke="#cb5757" stroke-linecap="round" stroke-width="2"/>
                            </g>
                        </svg>
                        </a>
                    </td>
                </tr>`)
            }

            $('select[name=protectedarea]').select2({placeholder:'--請選擇--',language: "zh-TW"})
            $('select[name=vegetation]').select2({language: "zh-TW"})
            $('select[name=county]').select2({language: "zh-TW"})
            //$('select').selectpicker();
            if (response.length > 0){
                $('#geodetic_datum').val(response[0][10])
            }

            // 刪除相機位置
            $('.removeButton').on('click', function(){
                let row = $(this).closest("tr");
                if ($(this).data('did')==undefined){
                // 如果是新增的相機位置 -> 直接刪除
                    row.remove();
                } else {
                // 如果是已存在的相機位置 -> 後端刪除
                    $.ajax({
                        type: 'GET',
                        url: "/delete_dep_sa",
                        data: {'type': 'dep', 'id': $(this).data('did'), 'project_id': $('input[name=pk]').val()},
                        success: function (response) {
                            if (response.status=='exists'){
                                alert('欲刪除的相機位置下尚有影像，請先刪除影像或將影像搬移至其他相機位置')
                            } else if (response.status=='done') {
                                alert('已成功刪除')
                                row.remove();
                            }
                        },
                        error: function (response) {
                            alert('未知錯誤，請聯繫管理員');
                        }
                    })
                }
            })
        },
        error: function (response) {
        }
    })

}



/*
$('#studyarea-list div.studyarea-name').each(function(){
    if ($(this).text() != original_name){
    name_list.push($(this).text())
    }
});*/
    
/*
$('#editSaModal').on('shown.bs.modal', function() { 
    $('#editStudyArea').val($('.current_sa .studyarea-name').html());
    $('#editStudyArea-id').val($('.current_sa').attr('id'));
});

$('#editSaModal').on('hidden.bs.modal', function() { 
    $(".is-invalid").removeClass("is-invalid").removeClass("was-validated");
});*/


/*
function editSa(type){

    $(".is-invalid").removeClass("is-invalid").removeClass("was-validated");

    if (type=='edit'){
        let name = $('#editStudyArea').val();
        // 也有可能是sub
        let original_name = $('.current_sa .studyarea-name').html();
        name_list = []
        $('#studyarea-list div.studyarea-name').each(function(){
            if ($(this).text() != original_name){
            name_list.push($(this).text())
            }
        });
        if (name=='' ){
            $('#editStudyArea-feedback').html('樣區名稱為必填');
            $('#editStudyArea').addClass("is-invalid").addClass("was-validated");
        } else if (name_list.includes(name)){
            $('#editStudyArea-feedback').html('樣區名稱不得重複');
            $('#editStudyArea').addClass("is-invalid").addClass("was-validated");
        } else {
            
            $.ajax({
                type: 'GET',
                url: "/edit_sa",
                data: {'name': name, 'id': $('#editStudyArea-id').val()},
                success: function (response) {
                    // 修改左側列表名稱
                    $('.current_sa .studyarea-name').html(name)
                    // 修改右側大標
                    $('.sa-name').html(name)
                    $('#editSaModal').modal('hide');
                    alert('設定已儲存')
                },
                error: function (response) {
                    alert('未知錯誤，請聯繫管理員')
                }
            })
            
        }    
    } else {
        // delete
        $.ajax({
            type: 'GET',
            url: "/delete_dep_sa",
            data: {'type': 'sa', 'id': $('#editStudyArea-id').val(), 'project_id': $('input[name=pk]').val()},
            success: function (response) {
                if (response.status=='exists'){
                    alert('欲刪除的樣區下尚有影像，請先刪除影像或將影像搬移至其他樣區')
                } else if (response.status=='done') {
                    alert('已成功刪除')
                    $('.current_sa').parent().next('.collapse').remove()
                    $('.current_sa').parent('li').remove()
                    $('#editSaModal').modal('hide')
                    // 右側恢復起始
                    $('#initial-content').removeClass("d-none");
                    $('#deployment-list').addClass("d-none");
                }
            },
            error: function (response) {
                alert('未知錯誤，請聯繫管理員');
            }
        })
    }
    
}
*/


/*
function addSa(){
}

function addDeployment(){
}

function selectStudyArea(id, sa_name){    
}


function addDepolymentSubmit(){
}



*/

    /*
    $.ajax({
      type: 'GET',
      url: `/api/get_edit_info/?pk=${pk}&type=deployment`,
      success: function (response) {
        for (let i = 0; i < response.study_area.length; i++) {
            if (response.study_area[i].parent_id != null){
                $(`#collapse_${ response.study_area[i].parent_id }`).prepend(`<li>
                <div class="studyarea-click" data-parent="${ response.study_area[i].parent_id }" id="${ response.study_area[i].id }" 
                    data-said="${ response.study_area[i].id }" data-saname="${ response.study_area[i].name }">
                    <div class="studyarea-name d-inline-block">${ response.study_area[i].name }
                    </div>
                </div>
            </li>`);
            $('.studyarea-click').on('click',function(){
                let id = $(this).data('said');
                let sa_name = $(this).data('saname');
                getDep(id, sa_name)
            })
            $(`#collapse_${ response.study_area[i].parent_id }`).removeClass('d-none');
            
            } 
            //else {
            //    $(`#collapse_${ response.study_area[i].id }`).remove()
            //}
        }
        },
    })*/




/*
$('.studyarea-click').on('click',function(){
    let id = $(this).data('said');
    let sa_name = $(this).data('saname');
    getDep(id, sa_name)
})*/



/*
$('#addSaModal').on('hidden.bs.modal', function() { 
    $(".is-invalid").removeClass("is-invalid").removeClass("was-validated");
    $('#addStudyArea').val('');
});*/








