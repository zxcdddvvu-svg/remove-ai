# Run the web interface on Google Colab

The project includes a Colab launcher that starts the normal HTTP service and
embeds the existing upload interface directly in the notebook.

Run these cells in order:

```python
!git clone https://github.com/daysihandy4288-a11y/watermarks-remover-colab.git
%cd /content/watermarks-remover-colab
!apt-get update -qq
!apt-get install -y -qq exiftool qpdf ffmpeg
```

```python
from colab_launcher import launch

server = launch(height=800)
```

To open the interface in a separate browser tab instead:

```python
from colab_launcher import launch

server = launch(window=True)
```

Keep the Colab runtime connected while using the interface. Uploaded and
cleaned files are temporary, so download the result before the runtime ends.

To stop a server started by the launcher:

```python
if server is not None:
    server.terminate()
```
