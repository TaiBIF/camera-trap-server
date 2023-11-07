/*
* TODO: CSP, src-inine in Chart.min.js, uikit.min.js
*/
const domReady = () => {
  "use strict";

    fetch('/api/dashboard/app_ver/')
    .then(resp => resp.json())
    .then(results => {
      console.log(results);

      const chartAppVer = document.getElementById('chart-app-ver');
      new Chart(chartAppVer, {
        type: 'bar',
        data: {
          labels: results.labels.map( x => x ),
          datasets: [{
            label: "上傳照片數",
            backgroundColor: ["#39f", "#895df6", "#3cba9f", "#e8c3b9", "#c45850"],
            data: results.data,
          }]
        },
        options: {
          maintainAspectRatio: false,
          responsiveAnimationDuration: 500,
          legend: {
            display: false
          },
          animation: {
            duration: 2000
          },
          title: {
            display: true,
            text: 'Images by App versions'
          }
        }
      });
    })

  fetch('/api/dashboard/recently/')
    .then(resp => resp.json())
    .then(results => {
      console.log(results);
      const chartRecently = document.getElementById('chart-recently');
      new Chart(chartRecently, {
        type: 'line',
        data: {
          labels: results.labels,
          datasets: [{
            data: results.data,
            label: 'Image annotations',
            borderColor: "#c45850",
            fill: false
          }, {
            data: results.data_has_storage,
            label: 'Image Uploaded to S3',
            borderColor: "#e8c3b9",
            fill: false
          }]
        },
        options: {
          maintainAspectRatio: false,
          responsiveAnimationDuration: 500,
          animation: {
            duration: 2000
          },
          title: {
            display: true,
            text: '# of Data Uploads Recently'
          }
        }
      });
    });

  fetch('/api/dashboard/top3/')
    .then(resp => resp.json())
    .then(results => {
      console.log(results);
      const labels = results.labels.map( x => { return (x === '0000') ? '<2000' : x});
      const chartData = document.getElementById('chart-data');
      new Chart(chartData, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [{
            data: results.projects[0].data,
            label: results.projects[0].name,
            borderColor: "#39f",
            fill: false
          }, {
            data: results.projects[1].data,
            label: results.projects[1].name,
            borderColor: "#895df6",
        fill: false
      }, {
        data: results.projects[2].data,
        label: results.projects[2].name,
        borderColor: "#3cba9f",
        fill: false
          }]
        },
        options: {
          maintainAspectRatio: false,
          responsiveAnimationDuration: 500,
          animation: {
            duration: 2000,
          },
          title: {
            display: true,
            text: 'Project data per year'
          }
        }
      });
    })
}

(function () {
  document.addEventListener('DOMContentLoaded', domReady, false);
})();
