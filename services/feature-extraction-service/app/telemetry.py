from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

# Setup basic TracerProvider
provider = TracerProvider()
exporter = InMemorySpanExporter()
processor = SimpleSpanProcessor(exporter)
provider.add_span_processor(processor)

# Register the provider
trace.set_tracer_provider(provider)

def get_tracer():
    return trace.get_tracer("feature-extraction-service")
