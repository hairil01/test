document.addEventListener('DOMContentLoaded', function() {
    var data = "{{ data }}";
    
    if (data === "Hello, World!") {
        // Show the snackbar
        var snackbar = document.getElementById('snackbar');
        snackbar.innerHTML = data;
        snackbar.classList.add('show');

        // Hide the snackbar after 10 seconds
        setTimeout(function() {
            snackbar.classList.remove('show');
        }, 10000);
    }
});
