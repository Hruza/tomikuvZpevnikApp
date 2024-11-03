import time


def log_request(request, processing_time, view_time=None, render_time=None):
    additional_msg = []
    if not view_time is None:
        additional_msg.append(f"{view_time*1000:.2f}ms to create view")
    if not render_time is None:
        additional_msg.append(f"{render_time*1000:.2f}ms to render view")

    additional_msg = f" ({' '.join(additional_msg)})" if len(additional_msg) > 0 else ""
    print(
        f"Request to {request.path} took {processing_time*1000:.2f}ms{additional_msg}."
    )


class Timing:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        self.start_time = time.time()
        self.view_time = None
        self.render_time = None
        response = self.get_response(request)

        processing_time = time.time() - self.start_time
        log_request(request, processing_time, self.view_time, self.render_time)

        return response

    def process_template_response(self, request, response):
        pre_render_time = time.time()
        self.view_time = pre_render_time - self.start_time
        response = response.render()
        self.render_time = time.time() - pre_render_time
        return response
