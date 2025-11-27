import io
from typing import Type, Optional, Literal
import requests
from pydantic import BaseModel
from dotmate.view.image import ImageView, ImageParams
from PIL import Image, ImageDraw


class CopperPriceParams(BaseModel):
    api_url: Optional[str] = None  # Optional API endpoint for fetching copper price
    title: Optional[str] = "沪铜主连"  # Default title
    link: Optional[str] = None
    border: Optional[int] = None
    dither_type: Optional[Literal["DIFFUSION", "ORDERED", "NONE"]] = "NONE"
    dither_kernel: Optional[
        Literal[
            "THRESHOLD",
            "ATKINSON",
            "BURKES",
            "FLOYD_STEINBERG",
            "SIERRA2",
            "STUCKI",
            "JARVIS_JUDICE_NINKE",
            "DIFFUSION_ROW",
            "DIFFUSION_COLUMN",
            "DIFFUSION2_D",
        ]
    ] = None


class CopperPriceView(ImageView):
    """View handler for displaying copper futures price information as an image."""

    def __init__(self, client, device_id: str):
        super().__init__(client, device_id)
        self.custom_font_name = "Hack-Bold"

    @classmethod
    def get_params_class(cls) -> Type[BaseModel]:
        return CopperPriceParams

    def _fetch_copper_price(self, api_url: Optional[str]) -> dict:
        """Fetch copper price data from API endpoint.

        Expected API response format:
        {
            "price": 87070.00,
            "change": 380.00,
            "change_percent": 0.44,
            "currency": "元"
        }
        """
        if not api_url:
            # Return mock data for testing/demo purposes
            return {
                "price": 87070.00,
                "change": 380.00,
                "change_percent": 0.44,
                "currency": "元"
            }

        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"API Error fetching copper price: {e}")
            # Return default data on error
            return {
                "price": 0.00,
                "change": 0.00,
                "change_percent": 0.00,
                "currency": "元"
            }

    def _format_price(self, price: float) -> str:
        """Format price with proper decimal places."""
        return f"{price:.2f}"

    def _format_change(self, change: float, change_percent: float) -> tuple[str, bool]:
        """Format change value and percentage, return (formatted_string, is_positive)."""
        is_positive = change >= 0
        sign = "+" if is_positive else ""

        change_str = f"{sign}{change:.2f}"
        percent_str = f"{sign}{change_percent:.2f}%"

        return f"{change_str} {percent_str}", is_positive

    def _generate_price_image(
        self,
        price_data: dict,
        title: str
    ) -> bytes:
        """Generate a 296x152 PNG image with copper price information."""
        width, height = 296, 152
        image = Image.new("1", (width, height), 1)  # 1-bit mode, 1=white, 0=black
        draw = ImageDraw.Draw(image)

        try:
            # Extract data
            price = price_data.get("price", 0.00)
            change = price_data.get("change", 0.00)
            change_percent = price_data.get("change_percent", 0.00)
            currency = price_data.get("currency", "元")

            # Format values
            price_str = self._format_price(price)
            change_str, is_positive = self._format_change(change, change_percent)

            # Font sizes
            title_font_size = 20
            price_font_size = 36
            currency_font_size = 18
            change_font_size = 16
            label_font_size = 14

            # Get fonts
            title_font = self._get_font(title_font_size)
            price_font = self._get_font(price_font_size)
            currency_font = self._get_font(currency_font_size)
            change_font = self._get_font(change_font_size)
            label_font = self._get_font(label_font_size)

            # Draw title at top
            bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = bbox[2] - bbox[0]
            title_x = (width - title_width) // 2
            draw.text((title_x, 10), title, fill=0, font=title_font)

            # Draw main price in center
            price_y = 50
            bbox = draw.textbbox((0, 0), price_str, font=price_font)
            price_width = bbox[2] - bbox[0]

            # Calculate currency text width
            bbox_currency = draw.textbbox((0, 0), currency, font=currency_font)
            currency_width = bbox_currency[2] - bbox_currency[0]

            # Calculate total width and center position
            total_width = price_width + currency_width + 5  # 5px spacing
            start_x = (width - total_width) // 2

            # Draw price and currency
            draw.text((start_x, price_y), price_str, fill=0, font=price_font)
            draw.text((start_x + price_width + 5, price_y + 8), currency, fill=0, font=currency_font)

            # Draw change information
            change_y = 100

            # Add triangle indicator
            triangle = "▲" if is_positive else "▼"
            change_text = f"{triangle} {change_str}"

            bbox = draw.textbbox((0, 0), change_text, font=change_font)
            change_width = bbox[2] - bbox[0]
            change_x = (width - change_width) // 2
            draw.text((change_x, change_y), change_text, fill=0, font=change_font)

            # Draw additional info line (trading status)
            info_y = 125
            info_text = "交易中"  # Trading
            bbox = draw.textbbox((0, 0), info_text, font=label_font)
            info_width = bbox[2] - bbox[0]
            info_x = (width - info_width) // 2
            draw.text((info_x, info_y), info_text, fill=0, font=label_font)

            # Convert to PNG binary data
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            buffer.seek(0)
            return buffer.read()

        except Exception as e:
            raise Exception(f"Error generating copper price image: {e}")

    def execute(self, params: BaseModel) -> None:
        """Generate copper price image and send to device."""
        price_params = CopperPriceParams(**params.model_dump())

        try:
            # Fetch copper price data
            price_data = self._fetch_copper_price(price_params.api_url)

            # Generate image
            image_data = self._generate_price_image(
                price_data,
                price_params.title
            )

            # Create ImageParams and use parent execute
            image_params = ImageParams(
                image_data=image_data,
                link=price_params.link,
                border=price_params.border,
                dither_type=price_params.dither_type,
                dither_kernel=price_params.dither_kernel,
            )

            # Use parent's execute method
            super().execute(image_params)

        except Exception as e:
            print(f"Error in CopperPriceView: {e}")
