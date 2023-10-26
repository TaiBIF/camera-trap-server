$(function () {
  const absentModal = document.getElementById('absent-modal');
  const calendarModal = document.getElementById('calendar-modal');
  /*
  const absentModal = document.getElementById('absent-modal');
  absentModal.style.display = 'none';
  const calendarModal = document.getElementById('calendar-modal');
  calendarModal.style.display = 'none';
  const calendarHack1 = document.getElementById('calendar-hack1');
  calendarHack1.style.margin = '4px 20px 10px 20px';
  const calendarHack2 = document.getElementById('calendar-hack2');
  calendarHack2.style.marginLeft = '20px';
  const calendarHack3 = document.getElementById('calendar-hack3');
  calendarHack3.style.margin = '20px 0px 20px 0px';
  const calendarTripList = document.getElementById('calendar-trip-list');
  calendarTripList.style.margin = '4px 0px 0px 30px';
*/
    let gapChoices = [];
    if ($('input[name=get-year]').val()){
        $.ajax({
            type: 'GET',
            url: `/api/get_gap_choice/`,
            success: function (response) {
                 gapChoices = response;
            }
        })
    }

    $('[data-toggle="tooltip"]').tooltip()
    $('.month-detail').click((e)=>{
      const data = JSON.parse(e.target.dataset.detail);
      //console.log(data);
      $('#detail-modal-title').html(`${data[0]}年${data[1]}月 | 相機位置: ${data[2]}`);
      $('#detail-modal-tbody').empty();
      $('#detail-modal-list').empty();
      $('#detail-modal-count').html(data[3]);
      $('#detail-modal-days').html(data[4]);
      $('#detail-modal-ratio').html((data[3] * 100.0 / data[4]).toFixed(2));
 
      for (let i=0; i<data[5].length; i++) {
        let cols = '';
        for (let j=0; j<data[5][i].length; j++) {
          let day = '';
          let cls = 'table-light';
          if (data[5][i][j] > 0) {
            day = data[5][i][j];
            cls = (data[6][day-1] > 0) ? 'table-success' : 'table-danger';
          } else {
            day = '';
          }
          cols += `<td class="${cls}" data-day="${day}" data-month="${data[1]}">${day}</div></td>`;
        }
        $('#detail-modal-tbody').append(`<tr>${cols}</tr>`);
      }
      for (let i=0; i<data[7].length; i++) {
        $('#detail-modal-list').append(`<li class="list-group-item">${data[7][i][0]} ~ ${data[7][i][1]}</li>`);
      }
      //$('.ct-calendar-day').on('click', function(e){
      //console.log(e.target.dataset['day'], e.target.dataset['month']);
      //})
    });
    $('.deployment-gap').click((e)=>{
      const name = e.target.dataset.name;
      const caused = e.target.dataset.caused;
      $('#gap-modal-title').html(`相機位置: ${name}`);
      $('#gap-modal-label').html(e.target.dataset.gaplabel);
 
      $('#form-gap-select').val('');
      $('#form-gap-text').val('');
 
      if (gapChoices.indexOf(caused) >=0 ) {
        $('#form-gap-select').val(caused);
      } else {
        $('#form-gap-text').val(caused);
      }
 
      $('#form-gap-id').val(e.target.dataset.gapid);
      $('#form-gap-start').val(e.target.dataset.gapstart);
      $('#form-gap-end').val(e.target.dataset.gapend);
      $('#form-gap-deployment-id').val(e.target.dataset.deploymentid);
    });
 
    $('#btn-gap-submit').click((e)=>{
      const payload = {
        text: $('#form-gap-text').val(),
        choice: $('#form-gap-select').val(),
        gapId: $('#form-gap-id').val(),
        range: [parseInt($('#form-gap-start').val(), 10), parseInt($('#form-gap-end').val(), 10)],
        deploymentId: $('#form-gap-deployment-id').val(),
        year: $('input[name=get-year]').val()
      };
 
      const host = `${window.location.protocol}//${window.location.host}`;
      let url = `${host}/api/deployment_journals/`;
      if ($('#form-gap-id').val()) {
        const gapId = parseInt($('#form-gap-id').val(), 10);
        url = `${url}${gapId}/`;
      }
      console.log(url, (payload.gapId) ? 'PUT' : 'POST');
      fetch(url, {
        method: (payload.gapId) ? 'PUT' : 'POST',
        mode: 'cors',
        headers: {
          'content-type': 'application/json'
        },
        body: JSON.stringify(payload),
      }).then((resp) => {
        if (!resp.ok) {
          console.error(resp.status);
        }
        return resp.json()
      }).then((data) => {
        //console.log(data);
        location.reload();
      });
    });


  $('.absent-btn').on('click',(e) => {
    console.log(e, e.target.dataset)
    $('.absent-pop').fadeIn()
    const name = e.target.dataset.name
    const caused = e.target.dataset.caused
    $('#absent-title').html(`相機位置: ${name}`)
    $('#absent-range-label').html(`範圍: ${e.target.dataset.gaplabel}`)

    $('#absent-select').val('')
    $('#absent-text').val('')
    if (gapChoices.indexOf(caused) >=0 ) {
      $('#absent-select').val(caused)
    } else {
      $('#absent-text').val(caused)
    }
    $('#absent-id').val(e.target.dataset.gapid)
    $('#absent-start').val(e.target.dataset.gapstart)
    $('#absent-end').val(e.target.dataset.gapend)
    $('#absent-deployment-id').val(e.target.dataset.deploymentid)
  })

  $('#absent-submit').click((e)=>{
    const payload = {
      text: $('#absent-text').val(),
      choice: $('#absent-select').val(),
      gapId: $('#absent-id').val(),
      range: [parseInt($('#absent-start').val(), 10), parseInt($('#absent-end').val(), 10)],
      deploymentId: $('#absent-deployment-id').val(),
      year: $('input[name=get-year]').val()
    };
    const host = `${window.location.protocol}//${window.location.host}`;
      let url = `${host}/api/deployment_journals/`;
      if ($('#absent-id').val()) {
        const gapId = parseInt($('#absent-id').val(), 10);
        url = `${url}${gapId}/`;
      }
      console.log(url, (payload.gapId) ? 'PUT' : 'POST');
      fetch(url, {
        method: (payload.gapId) ? 'PUT' : 'POST',
        mode: 'cors',
        headers: {
          'content-type': 'application/json'
        },
        body: JSON.stringify(payload),
      }).then((resp) => {
        if (!resp.ok) {
          console.error(resp.status);
        }
        return resp.json()
      }).then((data) => {
        //console.log(data);
        location.reload();
      });
    });
  $('.xx').on('click',function (event) {
    $('.absent-pop').fadeOut();
  });
  $('#absent-cancel').on('click',function (event) {
    $('.absent-pop').fadeOut();
  });

  $('.data-btn').on('click',function (event) {
    $('#calendar-trip-list').empty()
    $('.calendar-pop').fadeIn()
    console.log('aeu');
    calendarModal.style.display = 'block';
    const data = JSON.parse(event.target.dataset.detail)
    $('#calendar-working-days').html(data[3]);
    $('#calendar-num-days').html(data[4]);
    $('#calendar-ratio').html((data[3] * 100.0 / data[4]).toFixed(2));
    $('#calendar-title').html(`${data[0]}年${data[1]}月 | 相機位置: ${data[2]}`)
    $('#table-calendar').empty()
    $('#table-calendar').append(`<tr><td>一</td><td>二</td><td>三</td><td>四</td><td>五</td><td>六</td><td>日</td></tr>`);
    for (let i=0; i<data[5].length; i++) {
      let cols = '';
      for (let j=0; j<data[5][i].length; j++) {
        let day = '';
        let cls = '';
        if (data[5][i][j] > 0) {
          day = data[5][i][j];
          cls = (data[6][day-1] > 0) ? 'green-bg' : 'red-bg';
        } else {
          day = ''
        }
        cols += `<td class="${cls}" data-day="${day}" data-month="${data[1]}">${day}</div></td>`
      }
      $('#table-calendar').append(`<tr>${cols}</tr>`)
    }
    for (let i=0; i<data[7].length; i++) {
      $('#calendar-trip-list').append(`<li class="list-group-item">${data[7][i][0]} ~ ${data[7][i][1]}</li>`);
    }
  });
  $('.calendar-pop .xx').on('click',function (event) {
    $('.calendar-pop').fadeOut();
  });
  $('#hide-calendar').on('click',function (event) {
    $('.calendar-pop').fadeOut();
  });
  $('#submit-button').on('click', (e) => {
    $('.loading-pop').removeClass('d-none')
    $('#filter-form').submit()
  })
})
