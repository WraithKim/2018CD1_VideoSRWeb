$(function () {
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

  function validate(data) {
    var maxFileSize = 4 * 1000 * 1000 * 1000,
    // acceptFileTypes follow 'accept' attribute in <input type="file"> form.
    acceptFileTypes = /^video\//i;
    if (data.files[0]['size'] > maxFileSize){
      setProgressBarFailed("File size too large");
      return false;
    }
    if (!acceptFileTypes.test(data.files[0]['type'])){
      setProgressBarFailed("Not supported file type");
      return false;
    }
    return true;
  }

  /*
   * Starts the upload for a file in uploaded_data container.
   */
  startUpload = function () {
    if (uploaded_data) {
      // reset, if upload process has interrupted. (can resume soon cause nginx-upload-module will respond with where to resume.)
      uploaded_data.data = null;
      uploaded_data.formData = {
        scale_factor: $("input[type='radio'][name='scale_factor']:checked").val(),
        csrfmiddlewaretoken: $("input[name='csrfmiddlewaretoken']").val()
      }
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
  setProgressBarFailed = function (message) {
    $('#progress').addClass('bg-danger');
    setProgressBar(100);
    $('#progress').text(message);
  }

  /*
  * Set progress bar style when upload has successed
  */
  setProgressBarSuccess = function (message) {
    $('#progress').addClass('bg-success');
    setProgressBar(100);
    $('#progress').text(message);
  }

  /*
  * Start/Resume this specific upload when this button is clicked
  */
  $('#start_upload').click(function () {
    startUpload();
  });

  $('#fileupload').fileupload({
    maxNumberOfFiles: 1,
    // https://github.com/fdintino/nginx-upload-module/issues/106
    // By this issue, you should send chunk one by on in order.
    sequentialUploads: true,
    // maxFileSize and acceptFileTypes are only supported by the UI Version
    // so I will use these validation in validate() manually.

    add: function (e, data) {
      $('#filename').text(data.files[0].name);
      if (validate(data)) {
        var progress = calculateProgress(data);
        $('#progress').attr('class', 'progress-bar');
        setProgressBar(progress);
        uploaded_data = data;
      } else {
        uploaded_data = undefined;
      }
    },

    done: function (e, data) {
      // if you want to see status code, use "var status = data.jqXHR.status;"
      // FIXME: 디버그 정보가 노출됨
      // var responseText = data.jqXHR.responseText || "업로드 완료";
      // setProgressBarSuccess(responseText);
      location.reload();
    },

    fail: function (e, data) {
      // if you want to see status code, use "var status = data.jqXHR.status;"
      // FIXME: 디버그 정보가 노출됨
      // var responseText = data.jqXHR.responseText || "업로드 오류";
      var responseText = "업로드 오류";
      setProgressBarFailed(responseText);
    },

    progress: function (e, data) {
      setProgressBar(calculateProgress(data));
    }
  });
});