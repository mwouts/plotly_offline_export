# Offline export of plotly plots

Javascript plots are beautiful, but at times you also need to export them to image files. For
instance,
- plots in emails are better displayed when in PNG format
- plots in high quality PDF presentations should come in PDF format.

In this repo we offer the offline export in python, based on the PhantomJS technology already used
in the R package [webshot|https://github.com/wch/webshot/] for the same purpose.

# How to use the offline export

We start with an offline, interactive plot

```
import plotly.graph_objs as go
import plotly.offline as offline
figure = {'data':[go.Scatter(x=range(5), y=[x**2 for x in range(5)])],
          'layout':go.Layout(title='Sample plot')}
offline.init_notebook_mode()
offline.iplot(figure, show_link=False)
```

Now you have to
* download the PhantomJS binary from http://phantomjs.org/
* clone this repo (`git clone https://github.com/mwouts/plotly_offline_export.git`)

and then you will be able to export the plot to a PNG image.

```
# Import offline export
import sys
sys.path.append('/home/mwouts/dev/plotly_offline_export/')
from plotly_offline_export import *
# Tell where to find phantomjs (not required if phantomjs is in the PATH)
set_phantomjs_path('/home/mwouts/bin')
# Export to PNG
export_plot(figure, 'test_export.png')
```

# Enriching the output of interactive plots

You may find it useful to enrich your interactive plots in jupyter notebooks with
alternative plain images.

For instance, if `plotly_offline_export` is configured with
```
init_output_formats(['js', 'png'])
```

Then
```
iplot(figure)
```

will include in the notebook both the javascript and the PNG representation of the plot.

If you plan to send the result of your notebook over email, then you can select the PNG image
over the javascript one with
```
jupyter nbconvert --to html --NbConvertBase.display_data_priority='["image/png", "text/html", "text/plain"]'
```

