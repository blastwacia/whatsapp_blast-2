// script.js

$(document).ready(function() {
    // Handle file upload
    $('#upload-button').click(function() {
        var file = $('#file-input')[0].files[0];
        var formData = new FormData();
        formData.append('file', file);

        $.ajax({
            url: '/upload',
            type: 'POST',
            data: formData,
            contentType: false,
            processData: false,
            success: function(response) {
                $('#upload-status').text(response.message);
            },
            error: function(error) {
                $('#upload-status').text('Error: ' + error.responseText);
            }
        });
    });

    // Handle WhatsApp login (QR code scanning)
    $('#whatsapp-login-button').click(function() {
        $('#login-status').text('Please scan the QR code to login.');
        $.ajax({
            url: '/login',
            type: 'GET',
            success: function(response) {
                $('#login-status').text('Logged in successfully!');
                $('#start-blasting-button').prop('disabled', false);  // Enable the start button
            },
            error: function(error) {
                $('#login-status').text('Login failed: ' + error.responseText);
            }
        });
    });

    // Handle start blasting
    $('#start-blasting-button').click(function() {
        var messageTemplate = $('#message-template').val();
        var filePath = $('#file-input')[0].files[0].name;

        $.ajax({
            url: '/start',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ file_path: filePath, message: messageTemplate }),
            success: function(response) {
                alert('Blasting completed successfully');
            },
            error: function(error) {
                alert('Error: ' + error.responseText);
            }
        });
    });
});
