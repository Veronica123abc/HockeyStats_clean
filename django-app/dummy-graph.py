import matplotlib.pyplot as plt
import io
from django.http import HttpResponse
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas


def render_barchart(heights):
    # Generate indices for each bar
    x = range(len(heights))

    # Create the bar chart
    fig, ax = plt.subplots()
    ax.bar(x, heights)

    # Add labels and title
    ax.set_xlabel('Bar Index')
    ax.set_ylabel('Height')
    ax.set_title('Bar Chart of Heights')

    return fig


def barchart_view(request):
    # Example list of heights; in a real app, you might get this from a form or database
    heights = [1.5, 2.3, 3.7, 4.1, 2.9]

    # Create the bar chart
    fig = render_barchart(heights)

    # Convert plot to PNG image
    canvas = FigureCanvas(fig)
    buf = io.BytesIO()
    canvas.print_png(buf)
    plt.close(fig)  # Close the figure after rendering to free memory

    # Return the response as an image
    response = HttpResponse(buf.getvalue(), content_type='image/png')
    buf.close()
    return response