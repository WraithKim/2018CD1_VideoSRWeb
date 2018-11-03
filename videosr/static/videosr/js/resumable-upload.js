$(function () {
  var hash, sessionId;

  /*
  * Hash function for generate 'session-id' header
  */
  hash = function (s, tableSize) {
    var a, b, h, i, j, ref;
    b = 27183;
    h = 0;
    a = 31415;
    for (i = j = 0, ref = s.length;
      (0 <= ref ? j < ref : j > ref); i = 0 <= ref ? ++j : --j) {
      h = (a * h + s[i].charCodeAt()) % tableSize;
      a = ((a % tableSize) * (b % tableSize)) % tableSize;
    }
    return h;
  };

  /*
  * Generate session-id using hash function
  */
  sessionId = function (filename) {
    return hash(filename, 16384);
  };

  var calculateProgress, setProgressBar, setProgressBarFailed, setProgressBarSuccess, startUpload, uploaded_data;
  /*
   * A simple method to calculate the progress for a file upload.
   */
  calculateProgress = function (data) {
    var value;
    value = parseInt(data.loaded / data.total * 100, 10) || 0;
    if (value > 100) return 100;
    else if(value < 0) return 0;
    return value;
  };

  /*
   * Starts the upload for a file in uploaded_data container.
   */
  startUpload = function () {
    if (uploaded_data) {
      // reset, if upload process has interrupted. (can resume soon cause nginx-upload-module will respond with where to resume.)
      uploaded_data.data = null;
      uploaded_data.submit();
    }
  };


  /*
  * Set progress bar with given progress(number)
  */
  setProgressBar = function (progress) {
    $('#progress').css("width", `${progress}\%`);
    $('#progress').text(`${progress}\%`);
  }

  /*
  * Set progress bar style when upload has failed
  */
  setProgressBarFailed = function () {
    $('#progress').addClass('bg-danger');
    setProgressBar(100)
    $('#progress').text(`Upload Rejected from server`);
  }

  /*
  * Set progress bar style when upload has successed
  */
  setProgressBarSuccess = function () {
    $('#progress').addClass('bg-success');
    setProgressBar(100)
    $('#progress').text(`Upload Complete`);
  }



  /*
  * Get cookie from user.
  * Use this function to get csrf token.
  */
  function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
  } 

  // Start/Resume this specific upload when this button is clicked
  $('#start_upload').click(function () {
    startUpload();
  });

  $('#resumable-upload').fileupload({
    maxNumberOfFiles: 1,
    maxFileSize: 4 * 1000 * 1000 * 1000,
    // https://github.com/fdintino/nginx-upload-module/issues/106
    // By this issue, you should send chunk one by on in order.
    sequentialUploads: true,
    acceptFileTypes: /(\.|\/)(avi|mp4|mov|wmv|flv)$/i,

    add: function (e, data) {
      $('#filename').text(data.files[0].name);

      // add headers you need
      data.headers || (data.headers = {});
      // data.headers['Session-ID'] = sessionId(data.files[0].name);
      data.headers['X-CSRFToken'] = getCookie('csrftoken');

      var progress = calculateProgress(data);
      setProgressBar(progress);
      uploaded_data = data;
    },

    done: function (e, data) {
      // if you want to see status code, use "var status = data.jqXHR.status;"
      setProgressBarSuccess()
    },

    fail: function (e, data) {
      // if you want to see status code, use "var status = data.jqXHR.status;"
      setProgressBarFailed()
    },

    progress: function (e, data) {
      setProgressBar(calculateProgress(data))
    }
  });
});