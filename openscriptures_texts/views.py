from django.http import HttpResponse
from openscriptures_texts.models import Work, Token


def index(request):
    html = "<html><head><style>span:hover {background:yellow; outline:solid 1px red;}</style></head><body>"    
    html += "<h1>Works</h1>"
    for work in Work.objects.all():
        html += work.title + "<br />"

    #html += "<h1>Structures</h1>"
    #for ts in TokenStructure.objects.all():
    #    html += ts.osis_id + "<br />"

    html += "<h1>Tokens</h1>"
    for token in Token.objects.all():
        if token.type == Token.WHITESPACE:
            if token.data == "\n\n":
                html += "<br><br>"
            else:
                html += token.data
        else:
            html += "<span id='t" + str(token.pk) + "'>"
            html += token.data
            html += "</span>"

    html += "</body></html>"

    #html = "<html><body>It is now %s.</body></html>" % now
    return HttpResponse(html)
