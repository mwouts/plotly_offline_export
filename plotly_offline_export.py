import os, tempfile, json
import subprocess, threading
import plotly
from IPython.utils import capture
from base64 import encodestring as base64_encode

__PLOTLY_OFFLINE_EXPORT_FORMATS = ['js', 'png']
__IMAGE_FORMATS = ['js', 'jpeg', 'png', 'pdf']
__PHANTOMJS_PATH = None
__DEFAULT_WIDTH = 1200
__DEFAULT_HEIGHT = 600


def set_phantomjs_path(phantomjs_path):
    """
    Tell plotly_offline_export where to find phantomjs.
    :param phantomjs_path: Path to phantomjs script.
    :return:
    """
    global __PHANTOMJS_PATH
    __PHANTOMJS_PATH = phantomjs_path


def init_output_formats(formats=['js', 'png']):
    """
    Select the display formats for plotly plots. Plots generated with iplot will come in the
    selected formats, however when displayed in jupyter notebook only one format will be
    represented.

    At the time of converting the notebook to a HTML or markdown file, use the
    --NbConvertBase.display_data_priority argument if you want a specific representation.

    For instance, if you want to drop the javascript representation, use:
    jupyter nbconvert --to html --NbConvertBase.display_data_priority=\
        '["image/png", "text/html", "text/plain"]'

    :param formats: A subset of ['js', 'png', 'jpeg', 'pdf']
    :return:
    """
    global __PLOTLY_OFFLINE_EXPORT_FORMATS
    for f in formats:
        if f not in __IMAGE_FORMATS:
            raise ValueError('The image format must be one of the '
                             'following: {}'.format(__IMAGE_FORMATS))

    __PLOTLY_OFFLINE_EXPORT_FORMATS = formats
    if 'js' in formats:
        plotly.offline.init_notebook_mode()


def export_plot(figure_or_data,
                image_files,
                show_link=False,
                image_width=__DEFAULT_WIDTH,
                image_height=__DEFAULT_HEIGHT,
                timeout=5,
                **kwargs):
    """
    Offline export of a plotly figure to one or multiple static files.
    :param figure_or_data:
    :param image_files: A list of image file names.
    :param show_link:
    :param image_width:
    :param image_height:
    :param timeout: Timeout, in seconds, on the conversion job.
    :param kwargs:
    :return:
    """
    # turn image_files into a list
    if not isinstance(image_files, list):
        if not isinstance(image_files, str):
            raise TypeError('image_files must either be a file name, or a list of file names')
        else:
            image_files = [image_files]

    for img_file in image_files:
        file_name, extension = os.path.splitext(img_file)
        if extension not in ['.{}'.format(e) for e in __IMAGE_FORMATS]:
            raise ValueError('The image extension must be one of the '
                             'following: {}'.format(__IMAGE_FORMATS))

    # Save plot as temporary HTML file
    html_file = tempfile.mktemp(suffix=".html")
    plotly.offline.plot(figure_or_data,
                        image_width=image_width,
                        image_height=image_height,
                        filename=html_file,
                        show_link=show_link,
                        auto_open=False)

    for img_file in image_files:
        if __PHANTOMJS_PATH is None:
            phantomjs = 'phantomjs'
        elif __PHANTOMJS_PATH.endswith('phantomjs'):
            phantomjs = __PHANTOMJS_PATH
        else:
            phantomjs = os.path.join(__PHANTOMJS_PATH, 'phantomjs')

        webshot = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               'webshot', 'inst', 'webshot.js')

        if not os.path.isfile(webshot):
            raise OSError('webshot.js script not found at {}'.format(webshot))

        try:
            process = subprocess.Popen([phantomjs,
                                        webshot,
                                        json.dumps(
                                            [{'url': html_file, 'file': img_file, 'delay': 0.2,
                                              'vwidth': image_width, 'vheight': image_height
                                              }])],
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError as e:
            raise OSError(
                'PhantomJS was not found. Please install it from http://phantomjs.org/ '
                'and either update your PATH environment variable or execute '
                'set_phantomjs_path')

        if timeout:
            timer = threading.Timer(timeout, process.kill)
            try:
                timer.start()
                out, err = process.communicate()
            finally:
                timer.cancel()
        else:
            out, err = process.communicate()

        if out:
            print(out)
        if err:
            raise Exception(err)

    os.remove(html_file)
    return


def iplot(figure_or_data,
          show_link=False,
          image_width=__DEFAULT_WIDTH,
          image_height=__DEFAULT_HEIGHT,
          **kwargs):
    if 'js' in __PLOTLY_OFFLINE_EXPORT_FORMATS:
        with capture.capture_output() as cap:
            plotly.offline.iplot(figure_or_data,
                                 image_width=image_width,
                                 image_height=image_height,
                                 show_link=show_link,
                                 **kwargs)
            rich_output = cap.outputs[0]
    else:
        rich_output = capture.RichOutput()

    remaining_formats = set(__PLOTLY_OFFLINE_EXPORT_FORMATS).difference(['js'])
    if not len(remaining_formats):
        rich_output.display()
        return

    image_files = [tempfile.mktemp(suffix=".{}".format(f)) for f in remaining_formats]
    export_plot(figure_or_data, image_files,
                show_link=show_link, image_width=image_width, image_height=image_height, **kwargs)

    for fmt, img_file in zip(remaining_formats, image_files):
        with open(img_file) as f:
            b64 = base64_encode(f.read())
            if fmt == 'pdf':
                rich_output.data['application/pdf'] = b64
            elif fmt == 'png':
                rich_output.data['image/png'] = b64
            elif fmt == 'jpeg':
                rich_output.data['image/jpeg'] = b64
            else:
                raise ValueError('The image format must be one of the '
                                 'following: {}'.format(__IMAGE_FORMATS))
        os.remove(img_file)

    rich_output.display()
