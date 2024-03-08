/*
 * Version: 0.2.1 (231018)
 *
 * Changes
 * - 0 2.2 fix: download button bugs
 * - 0.2.1 charts
 * - 0.2.0 refactor new layout, wish vanilla js and jQuery select2
 * - 0.1.7 React + Maturial UI
 */
import {
  fetchData,
  getE,
  getEon,
  createE,
  serialize,
  Paginator,
} from './search_utils.js';

const domReady = () => {
  "use strict";
  const projectOptions = [];
  const projectMap = {};
  let projectSeq = 1;
  let myChart = null;

  /*
   * jQuery parts
   * from designer's layout
   */

  // for csp: style-src
  const modal = getE('calc-description-modal');
  //modal.style.display = 'none';
  const downloadModal = getE('download-modal');
  //downloadModal.style.display = 'none';
  const firstProjectItem = getE('filter-project1-item');
  //firstProjectItem.children[0].style.display = 'none';
  const imageModal = getE('result-image-modal');
  //imageModal.style.display = 'none';

  $('.note-btn').on('click',function (event) {
    $('.note-pop').fadeIn();
    //$('body').css("overflow", "hidden");
  });
  $('.ok').on('click',function (event) {
    $('.pop-box').fadeOut();
    //$('body').css("overflow", "initial");
  });
  $('.xx').on('click',function (event) {
    // TODO: cannot open again, because base.js add "d-none" class on element
    $('.pop-box').fadeOut();
    //$('body').css("overflow", "initial");
  });

  // disable calendar icon click
  const dateCalBtn = document.getElementsByClassName("date-cal");
  for (let i=0;i<dateCalBtn.length; i++) {
    dateCalBtn[i].onclick = (e) => {
      e.preventDefault();
      e.stopPropagation();
    };
  }

//https://emailregex.com
function ValidateEmail(inputText){
    let mailformat = /(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])/
    if(inputText.match(mailformat)){
        $('#email-check').attr('fill', 'green');
        $('button.download').prop('disabled', false);
    } else {
        $('#email-check').attr('fill', 'lightgrey');
        $('button.download').prop('disabled', true);
    }
  }

  $("#download-modal-email").keyup(function () {
    ValidateEmail($(this).val())
  });
  /*
   * init form widget settings
   */
  const setLoading = (isLoading) => {
    const loadingPop = document.getElementsByClassName("loading-pop");
    if (loadingPop.length > 0) {
      if (isLoading === true) {
        loadingPop[0].classList.remove("d-none");
      } else {
        loadingPop[0].classList.add("d-none");
      }
    }
  };

  const downloadModalEmail = getE('download-modal-email');
  const downloadModalTitle = getE('download-modal-title');
  const downloadModalSubmit = getE('download-modal-submit');
  downloadModalSubmit.onclick = (e) => {
    if (downloadModalEmail.value) {
      if (downloadModalTitle.textContent === '下載篩選資料') {
        goResultDownload(downloadModalEmail.value);
      } else {
        const cleanData = prepareFilterData();
        goCalcDownload(cleanData, downloadModalEmail.value)
      }
    }
  }

  const page = new Paginator(0, 20);

  const date_locale = { days: ['周日', '周一', '周二', '周三', '周四', '周五', '周六'],
                    daysShort: ['日', '一', '二', '三', '四', '五', '六'],
                    daysMin: ['日', '一', '二', '三', '四', '五', '六'],
                    months: ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月'],
                    monthsShort: ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月'],
                    today: '今天',
                    clear: '清除',
                    dateFormat: 'yyyy-MM-dd',
                    timeFormat: 'HH:mm',
                    firstDay: 1};
  const start_date_picker = new AirDatepicker(
    '#start_date', {
      locale: date_locale,
      //onSelect: function onSelect(fd, date, inst) {
      //updateSpeciesPie();
      //}
  });
  const endDate = getE('end_date');
  let now = new Date();
  const endPlaceholder = now.toISOString().split('T')[0];
  endDate.setAttribute('placeholder', endPlaceholder)
  endDate.setAttribute('value', endPlaceholder)
  $('#filter-project1-studyarea').select2({
    data: [],
    placeholder: '請選擇',
  });
  $('#filter-project1-deployment').select2({
    data: [],
    placeholder: '請選擇',
  });

  const end_date_picker = new AirDatepicker(
    '#end_date', {
      locale: date_locale,
  });

  // default first project click
  const projectSelect = getE('filter-project1-project');
  projectSelect.onchange = (e) => {
    if (e.currentTarget.value && projectOptions.length > 0) {
      const selectedProjectId = e.target.value;
      fetchData(`/api/deployments?project_id=${selectedProjectId}`)
        .then(results => {
          $('#filter-project1-studyareas').empty().trigger('change');
          $('#filter-project1-studyareas').select2({
            data: results.data.map((v, i) => ({id: v.studyarea_id, text: v.name})),
            placeholder: '請選擇',
          });

          $('#filter-project1-deployments').empty().trigger('change');
          $('#filter-project1-deployments').select2({
            data: results.data.map((v, i) => ({
              children: v.deployments.map((v2, i2) => ({
                id: v2.deployment_id,
                text: v2.name,
              })),
              text: v.name})),
            placeholder: '請選擇',
          });
        });
    }
  };

  /*
   * fetch init options
   * species/projects/named_areas (county, protectedarea)
   */
  fetchData('/api/species')
    .then(results => {
      if (results) {
        $('#filter-species').select2({
          data: results.data.map((x)=>({id: x.id, text: x.name})),
          placeholder: '請選擇',
        });
      }
    });

  fetchData('/api/projects')
    .then(results => {
      if (results) {
        const firstProjectSelect = getE('filter-project1-project');
        const firstOption = createE('option');
        firstOption.textContent = '請選擇';
        firstOption.value = '';
        firstProjectSelect.appendChild(firstOption);
        for (const x of results.data) {
          projectOptions.push(x);
          projectMap[x.id] = { project: x };
          // project options
          const option = createE('option');
          option.setAttribute('value', x.id);
          option.textContent = x.name;
          firstProjectSelect.appendChild(option);
        }
      }
    });

  fetchData('/api/named_areas')
    .then(results => {
      if (results) {
        $('#filter-namedareas-county').select2({
          data: results.data.county.map((x)=>({id: x.id, text: x.name})),
          placeholder: '請選擇',
        });
        $('#filter-namedareas-protectedarea').select2({
          data: results.data.protectedarea.map((x)=>({id: x.id, text: x.name})),
          placeholder: '請選擇',
        });
      }
    });

  /*
   * create project filter box
   * use: clone, createElement and bind jQuery select2
   */
  getEon('filter-project-create-button', (e) => {
    e.preventDefault();
    const projectContainer = getE('filter-project-container');
    const newItem = firstProjectItem.cloneNode(true);
    newItem.children[0].style.display = 'block';
    newItem.children[0].onclick = (e) => {
      newItem.remove();
    }

    projectSeq++;
    newItem.children[1].children[1].textContent = projectSeq;
    newItem.children[3].remove();
    newItem.id = newItem.id.replace('filter-project1', `filter-project${projectSeq}`);

    let otherProjectSelect = newItem.children[2].children[0];
    let saID = `filter-project${projectSeq}-studyareas`;
    let depID = `filter-project${projectSeq}-deployments`;
    otherProjectSelect.id = otherProjectSelect.id.replace('filter-project1', `filter-project${projectSeq}`);
    otherProjectSelect.name = otherProjectSelect.name.replace('box_1_', `box_${projectSeq}_`);
    otherProjectSelect.onchange = (e) => {
      if (e.target.value && projectOptions.length > 0) {
        const selectedProjectId = e.target.value;
        fetchData(`/api/deployments?project_id=${selectedProjectId}`)
          .then(results => {
            $(`#${saID}`).empty().trigger('change');
            $(`#${saID}`).select2({
              data: results.data.map((v, i) => ({id: v.studyarea_id, text: v.name})),
              placeholder: '請選擇',
            });

            $(`#${depID}`).empty().trigger('change');
            $(`#${depID}`).select2({
              data: results.data.map((v, i) => ({
                children: v.deployments.map((v2, i2) => ({
                  id: v2.deployment_id,
                  text: v2.name,
                })),
                text: v.name})),
              placeholder: '請選擇',
            });
          });
      }
    };

    let inp2Box = createE('div');
    inp2Box.classList.add('inp2box');
    let inp2Box_1 = createE('div');
    inp2Box_1.classList.add('input-item');
    let sa = createE('select');
    sa.name = `box_${projectSeq}_studyareas`;
    sa.id = saID;
    sa.setAttribute('multiple', 'multiple');
    let inp2Box_2 = createE('div');
    inp2Box_2.classList.add('input-item');
    let dep = createE('select');
    dep.name = `box_${projectSeq}_deployments`;
    dep.id = depID;
    dep.setAttribute('multiple', 'multiple');
    inp2Box_1.appendChild(sa);
    inp2Box_2.appendChild(dep);
    inp2Box.appendChild(inp2Box_1);
    inp2Box.appendChild(inp2Box_2);
    newItem.appendChild(inp2Box);

    //$(`${newId}`).empty().trigger('change');
    $(sa.id).select2({
        placeholder: 'choose',
    })
    $(dep.id).select2({
        placeholder: 'choose',
    })
    projectContainer.appendChild(newItem);
  }); // end of getEon('filter-project-create-button')


  /*
   * pagination actions
   */
  getEon('filter-prev-page', () => {
    if (page.hasPrevious) {
      page.setPage(page.pageIndex-1);
      goSearch();
    }
  });
  getEon('filter-next-page', () => {
    if (page.hasNext) {
      page.setPage(page.pageIndex+1);
      goSearch();
    }
  });
  getEon('filter-num-per-page', (e) => {
    page.setPerPage(e.target.value);
    goSearch();
  });

  // handle search submit
  getEon('filter-submit', (e) => {
    e.preventDefault();
    goSearch();
  });

  const prepareFilterData = () => {
    let form = getE('filter-form');
    let data = new FormData(form);
    let obj = serialize(data);
    console.log('FormData: ', obj);

    let cd = {
      species: $('#filter-species').select2('data').map((x) => (x.text)),
      counties: $('#filter-namedareas-county').select2('data').map((x) => ({id: x.id, name: x.text})),
      protectedareas: $('#filter-namedareas-protectedarea').select2('data').map((x) => ({id: x.id, name: x.text})),
      keyword: obj.keyword,
      startDate: obj.start_date,
      endDate: obj.end_date,
      altitude: obj.altitude,
      altitudeOperator:  obj.altitudeOperator,
      projects: [],
    };

    // find projects
    for(let name in obj) {
      let re = /box_[0-9]+_project/g;
      if (name.match(re) && obj[name]) {
        let k = name.split('_');
        let saID = `filter-project${k[1]}-studyareas`;
        let depID = `filter-project${k[1]}-deployments`;
        cd['projects'].push({
          project: projectMap[obj[name]].project,
          studyareas: $(`#${saID}`).select2('data').map((x)=>({id: x.id, name: x.text})),
          deployments: $(`#${depID}`).select2('data').map((x)=>({id: x.id, name: x.text})),
        });
      }
    }
    console.log('cleaned:', cd);

    return cd;
  };

  /*
   * fetch server search API and render results
   * use FormData and jquery select2 to collect data
   */
  const goSearch = () => {

    const filterDumps = JSON.stringify(prepareFilterData());
    let paginationDumps = JSON.stringify({perPage: page.perPage, pageIndex: page.pageIndex});

    let url = `/api/search?filter=${filterDumps}&pagination=${paginationDumps}`;
    console.log('fetch:', url);

    setLoading(true);

    fetchData(encodeURI(url))
      .then(results => {
        if (results) {
          setLoading(false);
          // render results
          const tableWrapper = getE('search-result-table');
          const totalText = getE('search-result-total');
          const seqFrom = getE('search-result-from');
          const seqTo = getE('search-result-to');
          totalText.textContent = results.total;
          page.setTotal(results.total);
          seqFrom.textContent = page.startSequence;
          seqTo.textContent = page.endSequence;
          const tableData = document.getElementsByClassName('search-result-table-data');
          // remove reverse for HTMLCollection as a "live list"
          for(let i=tableData.length; i--;) {
            tableData[i].remove();
          }

          const columes = ['id', 'filename', 'species', 'datetime', 'project__name', 'studyarea__name', 'deployment__name', 'deployment__altitude', 'deployment__county', 'deployment__protectedarea'];

          for (let i=0; i<results.data.length; i++) {
            const rowData = results.data[i];
            const row = createE('tr');
            row.onclick = (e) => {
              console.log(e);
              imageModal.style.display = 'block';
              const imgElement = getE('image-modal-img');
              imgElement.setAttribute('src', rowData['media'].replace('-m', '-l'));
            }
            row.classList.add('search-result-table-data')
            const colElemSeq = createE('td');
            colElemSeq.textContent = (page.pageIndex * page.perPage) + parseInt(i+1);
            row.appendChild(colElemSeq);
            for (let col of columes) {
              const colElem = createE('td');
              colElem.textContent = rowData[col];
              row.appendChild(colElem);
            }
            const colElemMedia = createE('td');
            colElemMedia.innerHTML = `<img src=${rowData['media'].replace('-m', '-q')} height="60">`;
            row.appendChild(colElemMedia);
            tableWrapper.appendChild(row);
          }
        }
      })
      .catch((error) => {
        setLoading(false);
        alert(`錯誤: ${error}`);
      })
  } // end of goSearch

  getEon('calc-submit-download',  () => {
    const cleanData = prepareFilterData();
    if (cleanData.species && cleanData.species.length === 0) {
      alert('必須至少選一個物種');
      return;
    }
    // check login first
    fetchData('/api/check_login')
      .then(results => {
        if (results.messages) {
            alert(results.messages);
            if (results.redirect && results.redirect === true) {
              window.location.replace(window.location.origin+ "/personal_info");
            }
        } else {
          downloadModalTitle.textContent = '下載計算資料';
          downloadModal.style.display = 'block';
        }
      });
  });

  getEon('result-download-btn', () => {
    // check login first
    fetchData('/api/check_login')
      .then(results => {
        if (results.messages) {
            alert(results.messages);
            if (results.redirect && results.redirect === true) {
              window.location.replace(window.location.origin+ "/personal_info");
            }
        } else {
          downloadModalTitle.textContent = '下載篩選資料';
          downloadModal.style.display = 'block';
        }
      });
  });

  const goCalcDownload = (cleanData, email) => {
    const calcType = getE('calc-type');
    const calcSession = getE('calc-session');
    const calcImageInterval = getE('calc-image-interval');
    const calcEventInterval = getE('calc-event-interval');
    const calcFileFormat = getE('calc-file-format');

    const calcData = {
      calcType: calcType.value,
      session: calcSession.value,
      imageInterval: calcImageInterval.value,
      eventInterval: calcEventInterval.value,
      fileFormat: calcFileFormat.value,
    }
    const filterDumps = JSON.stringify(cleanData);
    const calcDumps = JSON.stringify(calcData);

    let url = `/api/search?filter=${filterDumps}&calc=${calcDumps}&download=1&email=${email}`;
    fetchData(url)
      .then(results => {
        console.log('calculated', results);
      })
      .catch((error) => {
        alert(`錯誤: ${error}`);
      })
  };


  const goResultDownload = (email) => {
    const filterDumps = JSON.stringify(prepareFilterData());
    const url = `/api/search?filter=${filterDumps}&email=${email}&downloadData=1`;
    setLoading(true);
    fetchData(url)
      .then(results => {
        console.log('download results!', results);
        setLoading(false);
      })
      .catch( error => {
        alert(`錯誤: ${error}`);
        setLoading(false);
      })
    alert('請求已送出');
  }

  getEon('calc-submit-chart',  () => {
    const calcChartType = getE('calc-chart-type');
    if (calcChartType.value === '') {
      return;
    }

    const cleanData = prepareFilterData();
    if (cleanData.species && cleanData.species.length === 0) {
      alert('必須至少選一個物種');
      return;
    }

    const calcType = getE('calc-type');
    const calcSession = getE('calc-session');
    const calcImageInterval = getE('calc-image-interval');
    const calcEventInterval = getE('calc-event-interval');

    //const chartTitle = getE('chart-title');
    //chartTitle.textContent = calcChartType.selectedOptions[0].textContent;

    const calcData = {
      calcType: 'chart',
      session: calcSession.value,
      imageInterval: calcImageInterval.value,
      eventInterval: calcEventInterval.value,
      chartType: calcChartType.value,
    }

    const filterDumps = JSON.stringify(cleanData);
    const calcDumps = JSON.stringify(calcData);
    let url = `/api/search?filter=${filterDumps}&calc=${calcDumps}`;
    setLoading(true);
    fetchData(url)
      .then(results => {
        console.log('calculated charts!', results);
        setLoading(false);
        const chartTitle = `${calcChartType.selectedOptions[0].textContent}`;
        const chartSubTitle = `物種: ${cleanData.species}`;
        if ('error' in results) {
          alert(results['error']['message']);
          // empty chart
          while( myChart.series.length > 0 ) {
            myChart.series[0].remove( false );
          }
          myChart.redraw();
         } else {
           goChart(results, chartTitle, chartSubTitle);
         }
      })
      .catch((error) => {
        setLoading(false);
        alert(`錯誤: ${error}`);
      })
  });


  const goChart = (chartData, title, subtitle) => {
    //const chartTitle = getE('chart-title');
    //chartTitle.textContent = calcChartType.selectedOptions[0].textContent;
    chartData = {
      ...chartData,
      title: {
        text: title,
        align: 'left'
      },
      subtitle: {
        text: subtitle,
        align: 'left'
      }
    }
    myChart = Highcharts.chart('calc-chart', chartData);
  } // end of goChart

}

(function () {
  document.addEventListener('DOMContentLoaded', domReady, false);
})();
