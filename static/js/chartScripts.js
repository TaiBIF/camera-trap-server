// Chart 1
// ========================================================================
var char1El = document.getElementById('chart1');
new Chart(char1El, {
  type: 'bar',
  data: {
    labels: ["Africa", "Asia", "Europe", "Latin America", "North America"],
    datasets: [{
      label: "Population (millions)",
      backgroundColor: ["#39f", "#895df6", "#3cba9f", "#e8c3b9", "#c45850"],
      data: [1478, 5267, 3600, 1900, 4700]
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
      text: 'Predicted world population (millions) in 2050'
    }
  }
});

// Chart 2
// ========================================================================
var char2El = document.getElementById('chart2');

new Chart(char2El, {
  type: 'line',
  data: {
    labels: [2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018],
    datasets: [{
      data: [2004, 2000, 3200, 1200, 3450, 2300, 2200, 1200, 900, 1450],
      label: "Africa",
      borderColor: "#39f",
      fill: false
    }, {
      data: [4500, 4800, 5200, 5000, 5200, 5500, 5900, 6500, 6800, 7200],
      label: "Asia",
      borderColor: "#895df6",
      fill: false
    }, {
      data: [3400, 3200, 2800, 5600, 4500, 3200, 3400, 3800, 4800, 4200],
      label: "Europe",
      borderColor: "#3cba9f",
      fill: false
    }, {
      data: [1200, 1100, 1250, 1200, 1300, 1450, 1300, 1200, 1320, 1350],
      label: "Latin America",
      borderColor: "#e8c3b9",
      fill: false
    }, {
      data: [600, 3400, 2000, 1200, 7500, 2300, 3200, 6000, 3400, 4500],
      label: "North America",
      borderColor: "#c45850",
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
      text: 'Sales per region'
    }
  }
});


// Chart 3
// ========================================================================
var char3El = document.getElementById('chart3');

new Chart(char3El, {
  type: 'horizontalBar',
  data: {
    labels: ["Africa", "Asia", "Europe", "Latin America", "North America"],
    datasets: [{
      label: "Population (millions)",
      backgroundColor: ["#39f", "#895df6", "#3cba9f", "#e8c3b9", "#c45850"],
      data: [900, 7000, 5700, 2800, 5600]
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
      text: 'Predicted activity in 2020'
    }
  }
});

// Chart 4
// ========================================================================
var char4El = document.getElementById('chart4');

new Chart(char4El, {
  type: 'radar',
  data: {
    labels: ["Africa", "Asia", "Europe", "Latin America", "North America"],
    datasets: [{
      label: "1950",
      fill: true,
      backgroundColor: "rgba(51,153,255,0.6)",
      borderColor: "rgba(51,153,255,0.2)",

      pointBorderColor: "#fff",
      pointBackgroundColor: "rgba(179,181,198,1)",
      data: [8.77, 55.61, 21.69, 6.62, 6.82]
    }, {
      label: "2050",
      fill: true,
      backgroundColor: "rgba(255,99,132,0.2)",
      borderColor: "rgba(255,99,132,1)",
      pointBorderColor: "#fff",
      pointBackgroundColor: "rgba(255,99,132,1)",
      pointBorderColor: "#fff",
      data: [25.48, 54.16, 7.61, 8.06, 4.45]
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
      text: 'Distribution in % of world population'
    }
  }
});

// Chart 4
// ========================================================================
var char5El = document.getElementById('chart5');

new Chart(char5El, {
    type: 'doughnut',
    data: {
      labels: ["Africa", "Asia", "Europe", "Latin America", "North America"],
      datasets: [
        {
          label: "Population (millions)",
          backgroundColor: ["#39f", "#895df6","#3cba9f","#e8c3b9","#c45850"],
          data: [2478,5267,734,784,433]
        }
      ]
    },
    options: {
      maintainAspectRatio: false,
      responsiveAnimationDuration: 500,
      animation: {
        duration: 2000
      },
      title: {
        display: true,
        text: 'Predicted world population (millions) in 2050'
      }
    }
});


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
            duration: 2000
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
