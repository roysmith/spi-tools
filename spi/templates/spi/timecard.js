$(document).ready(function() {

    var ctx = $(document)[0].getElementById('chart').getContext('2d');
    var chart = new Chart(ctx, {
	type: 'bubble',
	options: {
	    responsive: false
	},
	data: {
	    labels: ['January', 'February', 'March', 'April', 'May', 'June', 'July'],
	    datasets: [{
		label: '',
		backgroundColor: 'rgb(255, 99, 132)',
		borderColor: 'rgb(255, 99, 132)',
		data: [
		    {% for d in data %}
		    {x: {{ d.x }}, y: {{ d.y }}, r: {{ d.r }} / 4 },
		    {% endfor %}
		]
	    }]
	},
    });
});
