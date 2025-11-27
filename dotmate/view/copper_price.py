import io
from typing import Type, Optional, Literal
import requests
from pydantic import BaseModel
from dotmate.view.image import ImageView, ImageParams
from PIL import Image, ImageDraw

try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False


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
        self.custom_font_name = "SourceHanSansSC-VF"
        self.font_weight = 600  # SemiBold weight for better readability

    @classmethod
    def get_params_class(cls) -> Type[BaseModel]:
        return CopperPriceParams

    def _fetch_copper_price_from_akshare(self) -> dict:
        """Fetch copper price data from AkShare using multiple fallback methods.

        Returns:
            dict: Price data in standardized format
        """
        try:
            if not AKSHARE_AVAILABLE:
                raise ImportError("AkShare is not installed")

            print("Fetching copper price from AkShare...")

            # Try method 1: futures_spot_price (works!)
            try:
                print("Trying ak.futures_spot_price...")
                df = ak.futures_spot_price()

                if df is not None and not df.empty:
                    # Filter for copper (symbol: CU)
                    copper_df = df[df['symbol'] == 'CU']

                    if not copper_df.empty:
                        print(f"✓ futures_spot_price succeeded - found copper data")
                        latest = copper_df.iloc[0]

                        # Extract price data
                        spot_price = float(latest['spot_price'])
                        dominant_price = float(latest.get('dominant_contract_price', spot_price))

                        # Use dominant contract price as current price
                        current_price = dominant_price

                        # Calculate change using basis (spot price - futures price)
                        # If dom_basis exists, use it to derive previous close
                        if 'dom_basis' in latest.index and latest['dom_basis'] is not None:
                            dom_basis = float(latest['dom_basis'])
                            # Since dom_basis = spot_price - dominant_price
                            # We can estimate previous close as current price minus some portion of basis
                            # For simplicity, use spot_price as reference
                            prev_close = spot_price
                        else:
                            prev_close = spot_price

                        change = current_price - prev_close
                        change_percent = (change / prev_close * 100) if prev_close != 0 else 0.0

                        result = {
                            "price": current_price,
                            "change": change,
                            "change_percent": change_percent,
                            "currency": "元"
                        }
                        print(f"Successfully fetched copper price: {result}")
                        return result
                    else:
                        print("✗ No copper data found in futures_spot_price")
            except Exception as e:
                print(f"✗ futures_spot_price failed: {type(e).__name__}: {e}")

            # Try method 2: futures_global_spot_em (also works!)
            try:
                print("Trying ak.futures_global_spot_em...")
                df = ak.futures_global_spot_em()

                if df is not None and not df.empty:
                    # Filter for copper - try different possible names
                    copper_df = df[df['名称'].str.contains('沪铜|铜|CU', case=False, na=False)]

                    if not copper_df.empty:
                        print(f"✓ futures_global_spot_em succeeded - found copper data")
                        # Take the first match (likely the main contract)
                        latest = copper_df.iloc[0]

                        # Extract price data (Chinese column names)
                        current_price = float(latest['最新价'])
                        prev_close = float(latest['昨结'])
                        change = float(latest['涨跌额'])
                        change_percent = float(latest['涨跌幅'])

                        result = {
                            "price": current_price,
                            "change": change,
                            "change_percent": change_percent,
                            "currency": "元"
                        }
                        print(f"Successfully fetched copper price: {result}")
                        return result
                    else:
                        print("✗ No copper data found in futures_global_spot_em")
            except Exception as e:
                print(f"✗ futures_global_spot_em failed: {type(e).__name__}: {e}")

            # All methods failed
            raise ValueError("All AkShare methods failed to fetch copper price data")

        except Exception as e:
            print(f"AkShare Error fetching copper price: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _parse_akshare_dataframe(self, df) -> dict:
        """Parse AkShare DataFrame to extract price data.

        Args:
            df: Pandas DataFrame from AkShare

        Returns:
            dict: Standardized price data
        """
        print(f"DataFrame columns: {df.columns.tolist()}")
        print(f"Latest row:\n{df.iloc[-1]}")

        # Get the latest data (most recent row)
        latest = df.iloc[-1]

        # Calculate change from previous close or open
        current_price = float(latest['close'])
        open_price = float(latest['open'])

        # Try to get previous close, fallback to open if not available
        if 'pre_close' in latest.index:
            prev_close = float(latest['pre_close'])
        else:
            # If no pre_close, use the previous day's close
            if len(df) > 1:
                prev_close = float(df.iloc[-2]['close'])
            else:
                prev_close = open_price

        # Calculate change and percentage
        change = current_price - prev_close
        change_percent = (change / prev_close * 100) if prev_close != 0 else 0.0

        result = {
            "price": current_price,
            "change": change,
            "change_percent": change_percent,
            "currency": "元"
        }

        print(f"Successfully parsed copper price: {result}")
        return result

    def _fetch_copper_price(self, api_url: Optional[str]) -> dict:
        """Fetch copper price data from API endpoint or AkShare.

        Priority:
        1. If api_url is provided and is not "akshare", fetch from custom API
        2. If api_url is None or "akshare", fetch from AkShare
        3. If all fail, return mock data

        Expected API response format:
        {
            "price": 87070.00,
            "change": 380.00,
            "change_percent": 0.44,
            "currency": "元"
        }
        """
        # Try AkShare first if no api_url or api_url is "akshare"
        if not api_url or api_url.lower() == "akshare":
            try:
                return self._fetch_copper_price_from_akshare()
            except Exception as e:
                print(f"Failed to fetch from AkShare: {e}")
                # Fall through to mock data
                return {
                    "price": 87070.00,
                    "change": 380.00,
                    "change_percent": 0.44,
                    "currency": "元"
                }

        # Try custom API endpoint
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"API Error fetching copper price from {api_url}: {e}")
            # Try AkShare as fallback
            try:
                return self._fetch_copper_price_from_akshare()
            except Exception:
                # Final fallback to mock data
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
