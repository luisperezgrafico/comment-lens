function updateProgress() {
    fetch('/api/progress')
      .then(response => response.json())
      .then(data => {
        let statusText = '';
        if (data.status === 'idle') {
          statusText = 'Ready';
        } else if (data.status === 'analyzing') {
          statusText = `Analyzing comment batch ${data.current_chunk} of ${data.total_chunks}`;
        } else if (data.status === 'summarizing') {
          statusText = 'Creating comment insights';
        }
        document.getElementById('progress-status').innerText = statusText;
      })
      .catch(error => {
        console.error('Error fetching progress:', error);
      });
  }
  
  setInterval(updateProgress, 1000);
  