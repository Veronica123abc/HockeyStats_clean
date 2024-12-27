import matplotlib.pyplot as plt
import io
from django.http import HttpResponse
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from django.shortcuts import render


def render_barchart(heights):
    x = range(len(heights))
    fig, ax = plt.subplots()
    ax.bar(x, heights)
    ax.set_xlabel('Bar Index')
    ax.set_ylabel('Height')
    ax.set_title('Bar Chart of Heights')
    return fig


def render_piechart(heights):
    labels = [f"Item {i}" for i in range(1, len(heights) + 1)]
    fig, ax = plt.subplots()
    ax.pie(heights, labels=labels, autopct='%1.1f%%')
    ax.set_title('Pie Chart of Heights')
    return fig


def menu_view(request):
    return render(request, 'dummy/menu.html')

def dummy_view(request):
    chart_type = None
    if request.method == 'POST':
        chart_type = request.POST.get('chart_type')

    return render(request, 'dummy/dummy.html', {'chart_type': chart_type})


def dummy_image_view(request, chart_type):
    heights = [1.5, 2.3, 3.7, 4.1, 2.9]


    if chart_type == 'bar':
        fig = render_barchart(heights)
    elif chart_type == 'pie':
        fig = render_piechart(heights)

    # Convert the figure to PNG image
    canvas = FigureCanvas(fig)
    buf = io.BytesIO()
    canvas.print_png(buf)
    plt.close(fig)

    return HttpResponse(buf.getvalue(), content_type='image/png')

    #return render(request, 'dummy/dummy.html')

