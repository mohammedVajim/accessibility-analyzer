import subprocess
import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.template.loader import render_to_string
from weasyprint import HTML
import os
from openai import OpenAI


# Initialize OpenAI client (no indentation here)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Keep your key in .env
print(os.getenv("OPENAI_API_KEY"))


@csrf_exempt
def check_accessibility(request):
    if request.method == 'POST':
        url = request.POST.get('url')
        if not url:
            return JsonResponse({'error': 'URL is required'}, status=400)

        try:
            result = subprocess.run(
                ['node', 'scanner/node_script/accessibilityCheck.js', url],
                capture_output=True,
                text=True,
                check=True
            )
            output = json.loads(result.stdout)

            # Extract axe results
            violations = output.get('violations', [])
            passes = output.get('passes', [])
            incomplete = output.get('incomplete', [])
            inapplicable = output.get('inapplicable', [])

            # Calculate score and metadata
            total_issues = len(violations)
            score = max(0, 100 - total_issues)

            status_text = "Compliant" if score >= 95 else "NOT COMPLIANT"
            description = (
                "Your site meets accessibility standards 🎉" if score >= 95
                else "Your site may be at risk of accessibility lawsuit ⚠️"
            )

            context = {
                'score': score,
                'status_text': status_text,
                'description': description,
                'total_issues': total_issues,
                'critical_issues': len(violations) if violations else 0,
                'passed_audits': len(passes) if passes else 0,
                'manual_audits': len(incomplete) if incomplete else 0,
                'not_applicable': len(inapplicable) if inapplicable else 0,
                'violations': violations,
                # 'violations': json.dumps(violations),
                'passes': passes,
                'incomplete': incomplete,
                'inapplicable': inapplicable,

                # For JS modal (AI fixes)
                'violations_json': json.dumps(violations),
            }
            request.session["last_report_context"] = context

            return render(request, 'scanner/report.html', context)

        except subprocess.CalledProcessError as e:
            return JsonResponse({'error': e.stderr}, status=500)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON returned'}, status=500)

    return render(request, 'scanner/index.html')


def report_view(request):
    """Just renders the report page without running scan (for direct access)."""
    return render(request, 'scanner/report.html')

def checklist_view(request):
    return render(request, "scanner/checklist.html")


@csrf_exempt
def ai_fix_suggestion(request):
    """Return AI-powered fix suggestions for an accessibility issue."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode("utf-8"))
            issue_text = data.get("issue")

            if not issue_text:
                return JsonResponse({"error": "Issue text is required"}, status=400)

            # Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an accessibility expert."},
                    {"role": "user", "content": f"Suggest a fix for this accessibility issue: {issue_text}"}
                ]
            )

            suggestion = response.choices[0].message.content
            return JsonResponse({"suggestion": suggestion})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)


def download_report(request):
    """Generate and return PDF report with real scan results."""

    # 👇 Reuse the context stored in session or re-run scan
    context = request.session.get("last_report_context")
    if not context:
        return HttpResponse("No report data available. Please run a scan first.", status=400)

    html_string = render_to_string("scanner/report_pdf.html", context)
    pdf_file = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="accessibility_report.pdf"'
    return response
