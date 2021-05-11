$(document).ready(function() {

    var options = {
	responsive: true,
	maintainAspectRation: false,
	legend: {
	    display: true
	},
	layout: {
	    padding: {
		left: 15,
		right: 15,
		top: 15,
		bottom: 15
	    }
	},
	scales: {
	    yAxes: [
		{
		    display: true,
		    offset: false,
		    ticks: {
			min: 1,
			max: 7,
			stepSize: 7
		    }
		}
	    ],
	    xAxes: [
		{
		    display: true,
		    offset: false,
		    ticks: {
			min: 0,
			max: 24,
			stepSize: 24
		    }
		}
	    ]
	}
    };

    {% for userName, timecard in data.items() %}
    var ctx = $(document)[0].getElementById('chart-' + {{ userName|tojson }}).getContext('2d');
    var chart = new Chart(ctx, {
	type: 'bubble',
	options: options,
	data: {
	    datasets: [{
		backgroundColor: 'rgb(255, 99, 132)',
		borderColor: 'rgb(255, 99, 132)',
		label: {{ userName|tojson }},
		data: [
		    {% for t in timecard %}
		    {x: {{ t.x }}, y: {{ t.y }}, r: {{ t.r }} * 0.5 },
		    {% endfor %}
		]
	    }]
	},
    });
    {% endfor %}
});
