import typer
import requests
import os
import asciichartpy
import json
from rich.console import Console
from rich.table import Table
from rich import box
from dotenv import load_dotenv
from pathlib import Path

# 1. โหลด API Key จากไฟล์ .env
load_dotenv()

# 2. ตั้งค่า App
app = typer.Typer()
console = Console()
WATCHLIST_FILE = Path("watchlist.json")

def load_watchlist() -> list[str]:
    """Load watchlist symbols from local JSON file."""
    if not WATCHLIST_FILE.exists():
        return []

    try:
        with WATCHLIST_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return [str(s).upper() for s in data]
    except Exception:
        # ถ้าไฟล์พัง/อ่านไม่ได้ ให้เริ่มใหม่
        return []

    return []

def save_watchlist(symbols: list[str]) -> None:
    """Save watchlist symbols to local JSON file."""
    symbols = sorted(set(s.upper() for s in symbols))
    with WATCHLIST_FILE.open("w", encoding="utf-8") as f:
        json.dump(symbols, f, indent=2)

# Top 20 Companies by Market Cap
@app.command(name="list")
def show_list():
    """
    [Market] Show Top 20 Largest Companies (Market Cap).
    """
    api_key = os.getenv("ALPHA_VANTAGE_KEY")
    if not api_key:
        console.print("[red]Error: ALPHA_VANTAGE_KEY not found in .env[/red]")
        return

    # รายชื่อ 20 บริษัทที่ใหญ่ที่สุด (เรียงตาม Market Cap โดยประมาณ ณ ปัจจุบัน)
    # เนื่องจาก Alpha Vantage ไม่มี Endpoint นี้ เราจึงต้องกำหนด List เอง
    top_20_symbols = [
        "AAPL", "NVDA", "MSFT", "GOOGL", "AMZN", 
        "META", "TSLA", "BRK.B", "LLY", "AVGO", 
        "JPM", "V", "WMT", "XOM", "UNH", 
        "MA", "PG", "JNJ", "COST", "HD"
    ]

    console.print(f"[yellow]Fetching data for Top {len(top_20_symbols)} Market Cap Companies...[/yellow]")
    console.print("[dim]Note: Free API key allows 5 calls/min. Some data might be skipped.[/dim]\n")

    table = Table(title="Top 20 Companies by Market Cap")
    table.add_column("Rank", style="dim", justify="center", width=4)
    table.add_column("Symbol", style="bold cyan")
    table.add_column("Price", justify="right")
    table.add_column("Change", justify="right")
    table.add_column("Status", justify="right")

    limit_reached = False

    for idx, symbol in enumerate(top_20_symbols, 1):
        # ถ้าติด Limit ไปแล้ว ไม่ต้องยิง Request ต่อให้เสียเวลา
        if limit_reached:
            table.add_row(str(idx), symbol, "-", "-", "[red]API Limit[/red]")
            continue

        url = "https://www.alphavantage.co/query"
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": api_key
        }

        try:
            response = requests.get(url, params=params).json()
            
            # เช็คว่าติด Limit หรือไม่ (Alpha Vantage จะส่ง message มาบอก)
            if "Note" in response or "Information" in response:
                limit_reached = True
                table.add_row(str(idx), symbol, "-", "-", "[red]API Limit Hit[/red]")
                continue

            data = response.get("Global Quote", {})
            if not data:
                table.add_row(str(idx), symbol, "N/A", "N/A", "[yellow]Not Found[/yellow]")
                continue

            # ดึงข้อมูลราคา
            price = float(data.get("05. price", 0))
            change = float(data.get("09. change", 0))
            pct = data.get("10. change percent", "0%")

            # จัดสี
            color = "green" if change >= 0 else "red"
            price_str = f"${price:,.2f}"
            change_str = f"[{color}]{change:+.2f} ({pct})[/{color}]"

            table.add_row(str(idx), symbol, price_str, change_str, "[green]OK[/green]")

        except Exception:
            table.add_row(str(idx), symbol, "Error", "Error", "[red]Failed[/red]")

    console.print(table)
    
    if limit_reached:
        console.print("\n[bold red]⚠️  API Rate Limit Reached![/bold red]")
        console.print("[white]Alpha Vantage Free Tier allows only 5 requests per minute.[/white]")
        console.print("[dim]Wait 1 minute and try fetching specific stocks using: python app.py stock <SYMBOL>[/dim]\n")


# Stock Feature (Price & Chart)
@app.command()
def stock(symbol: str, plot: bool = typer.Option(False, "--plot", help="Show 30-day price chart")):
    """
    [Stock] Get stock price. Use --plot to see a history chart.
    Example: python app.py stock AAPL --plot
    """
    api_key = os.getenv("ALPHA_VANTAGE_KEY")
    if not api_key:
        console.print("[red]Error: ALPHA_VANTAGE_KEY not found in .env[/red]")
        return

    symbol = symbol.upper()
    
    # กรณีต้องการดูกราฟ (--plot)
    if plot:
        console.print(f"[yellow]Fetching historical data for {symbol}...[/yellow]")
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}"
        
        try:
            response = requests.get(url).json()
            data = response.get("Time Series (Daily)", {})
            
            if not data:
                console.print(f"[red]Error: No data found for {symbol}. (Check API limit)[/red]")
                return

            # ดึงราคาปิด (Close Price) ย้อนหลัง 30 วัน
            dates = list(data.keys())[:30]
            prices = [float(data[date]['4. close']) for date in dates]
            
            # กลับด้านข้อมูล (เพราะ API ให้มาแบบ ใหม่ -> เก่า แต่กราฟต้องวาด เก่า -> ใหม่)
            prices.reverse()

            # วาดกราฟ
            console.print(f"\n[bold green]📈 30-Day Price Chart: {symbol}[/bold green]")
            console.print(asciichartpy.plot(prices, {'height': 10}))
            console.print(f"[dim]Last Price: {prices[-1]} USD[/dim]\n")
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    # กรณีดูราคาปกติ (ไม่มี --plot)
    else:
        console.print(f"[yellow]Fetching price for {symbol}...[/yellow]")
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
        
        try:
            response = requests.get(url).json()
            data = response.get("Global Quote", {})
            
            if not data:
                console.print(f"[red]Error: Symbol '{symbol}' not found.[/red]")
                return

            table = Table(title=f"Stock Data: {symbol}")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Price", f"${data['05. price']}")
            table.add_row("Change", f"{data['09. change']} ({data['10. change percent']})")
            table.add_row("Volume", data['06. volume'])
            table.add_row("Previous Close", f"${data['08. previous close']}")
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

# Crypto Feature (Price & Market Cap OR Trending)
@app.command()
def crypto(
    option: str = typer.Argument(
        ..., 
        metavar="coin or 'trending'", 
        help="Choose one of the following:\n\n"
             "1. coin: Enter coin name (e.g. bitcoin) for price.\n\n"
             "2. 'trending': Type 'trending' to see Top-15 list."
    )
):
    """
    [Crypto] Get crypto price & market cap or see trending coins. Use --help for options.
    """
    # Recieve option from user
    option = option.lower()

    # see trending coins
    if option == "trending":
        url = "https://api.coingecko.com/api/v3/search/trending"
        console.print("[yellow]Fetching top-15 trending coins...[/yellow]")
        
        try:
            response = requests.get(url)
            data = response.json()
            coins = data.get("coins", [])

            if not coins:
                console.print("[red]No trending data found.[/red]")
                return

            table = Table(title="Top-15 Trending Coins (CoinGecko)")
            table.add_column("Rank", style="magenta", justify="center")
            table.add_column("Name", style="white")
            table.add_column("Symbol", style="cyan")
            table.add_column("Market Cap Rank", style="green", justify="right")
            table.add_column("Price (USD)", style="yellow", justify="right")
            
            for c in coins:
                item = c['item']
                rank = str(item.get('score', 0) + 1)
                name = item.get('name')
                symbol = item.get('symbol')
                mc_rank = str(item.get('market_cap_rank', 'N/A'))
                
                raw_price = item.get("data", {}).get("price", 0)
                
                try:
                    price_val = float(raw_price)
                    price_usd = f"${price_val:,.2f}"
                    
                except (ValueError, TypeError):
                    price_usd = "N/A"
                
                table.add_row(rank, name, symbol, mc_rank, price_usd)
                
            console.print(table)
            console.print("[dim]Source: CoinGecko API[/dim]\n")
            
        except Exception as e:
            console.print(f"[red]Error fetching trending: {e}[/red]")
            
        return

    # see specific coin data
    console.print(f"[yellow]Fetching data for {option}...[/yellow]")
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": option
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if not data:
            console.print(f"[red]Error: Coin '{option}' not found. Please use the full Coin ID (e.g., 'bitcoin' not 'BTC')[/red]")
            return

        coin_data = data[0]

        table = Table(title=f"Crypto Data: {coin_data['name']} ({coin_data['symbol'].upper()})")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Current Price", f"${coin_data['current_price']:,}")
        table.add_row("Market Cap", f"${coin_data['market_cap']:,}")
        table.add_row("24h High", f"${coin_data['high_24h']:,}")
        table.add_row("24h Low", f"${coin_data['low_24h']:,}")
        
        change_24h = coin_data.get('price_change_percentage_24h')
        change_style = "green" if change_24h is not None and change_24h >= 0 else "red"
        change_display = f"{change_24h}%" if change_24h is not None else "N/A"
        
        table.add_row("24h Change", f"[{change_style}]{change_display}[/{change_style}]")

        console.print(table)
        console.print(f"[dim]Last Updated: {coin_data['last_updated']}[/dim]\n")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

# ดูข่าวสาร
# 4. Global News Feed
@app.command()
def news(category: str = typer.Option("business", "--category", help="Choose category: business, entertainment, general, health, science, sports, technology")):
    """
    [News] Get top headlines with links.
    Example: python app.py news --category technology
    """
    # 1. รายชื่อหมวดหมู่ที่ถูกต้อง
    valid_categories = ["business", "entertainment", "general", "health", "science", "sports", "technology"]

    # 2. ตรวจสอบว่าผู้ใช้พิมพ์หมวดหมู่ถูกไหม
    if category not in valid_categories:
        console.print(f"[red]❌ Error: '{category}' is not a valid category.[/red]")
        console.print(f"[yellow]💡 Available categories are: {', '.join(valid_categories)}[/yellow]")
        return

    # 3. ตรวจสอบ API Key
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        console.print("[red]Error: NEWS_API_KEY not found in .env[/red]")
        return

    console.print(f"[yellow]Fetching top {category} news...[/yellow]")
    url = f"https://newsapi.org/v2/top-headlines?category={category}&language=en&apiKey={api_key}"

    try:
        response = requests.get(url).json()

        # เช็คว่า API ส่ง Error กลับมาไหม
        if response.get("status") == "error":
            console.print(f"[red]API Error: {response.get('message')}[/red]")
            return

        articles = response.get("articles", [])

        if not articles:
            console.print(f"[red]No news found for category '{category}'.[/red]")
            return

        # 4. สร้างตารางแสดงผล
        table = Table(title=f"Top News: {category.capitalize()}")
        table.add_column("Source", style="cyan", width=15)
        table.add_column("Title & Link", style="white") # คอลัมน์นี้ใส่ทั้งชื่อและลิงก์

        # ดึงแค่ 5 ข่าวแรก
        for article in articles[:5]:
            source = article['source']['name']
            title = article['title']
            link = article['url']

            # จัดรูปแบบข้อความ:
            # - [link={link}]{title}[/link] : ทำให้ชื่อข่าวคลิกได้ (ใน VS Code กด Ctrl+Click)
            # - \n : ขึ้นบรรทัดใหม่
            # - [dim blue]...[/dim blue] : แสดง URL สีฟ้าจางๆ ด้านล่าง
            display_text = f"[link={link}]{title}[/link]\n[dim blue]🔗 {link}[/dim blue]"

            table.add_row(source, display_text)
            table.add_section() # ขีดเส้นคั่นระหว่างข่าวเพื่อให้อ่านง่าย

        console.print(table)
        console.print(f"[dim]Tip: Ctrl+Click on the title to open in browser.[/dim]")

    except Exception as e:
        console.print(f"[red]Error fetching news: {e}[/red]")
        
# ดูอัตราแลกเปลี่ยนเงิน
@app.command()
def forex(
    from_currency: str = typer.Argument(..., help="FROM currency code, e.g. USD"),
    to_currency: str = typer.Argument(..., help="TO currency code, e.g. THB"),
):
    """
    [Forex] Check currency exchange rate between two currencies.
    Example:
      python app.py forex USD THB
    """
    api_key = os.getenv("ALPHA_VANTAGE_KEY")
    if not api_key:
        console.print("[red]Error: ALPHA_VANTAGE_KEY not found in .env[/red]")
        return

    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    console.print(f"[yellow]Fetching FX rate {from_currency} → {to_currency}...[/yellow]")

    # Realtime rate
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "CURRENCY_EXCHANGE_RATE",
        "from_currency": from_currency,
        "to_currency": to_currency,
        "apikey": api_key,
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()

        key = "Realtime Currency Exchange Rate"
        if key not in data:
            console.print("[red]Error: Cannot get exchange rate from API.[/red]")
            console.print(f"[dim]{data}[/dim]")
            return

        info = data[key]
        rate = float(info["5. Exchange Rate"])
        last_refreshed = info.get("6. Last Refreshed", "N/A")

        from_name = info.get("1. From_Currency Name", from_currency)
        to_name = info.get("3. To_Currency Name", to_currency)

        # เลือกธง
        flag_from = "🇺🇸" if from_currency == "USD" else ""
        flag_to = "🇹🇭" if to_currency == "THB" else ""

        # 1-day change %  
        change_str = "N/A"
        try:
            daily_url = "https://www.alphavantage.co/query"
            daily_params = {
                "function": "FX_DAILY",
                "from_symbol": from_currency,
                "to_symbol": to_currency,
                "outputsize": "compact",
                "apikey": api_key,
            }
            daily_resp = requests.get(daily_url, params=daily_params, timeout=10).json()
            ts = daily_resp.get("Time Series FX (Daily)", {})
            dates = sorted(ts.keys(), reverse=True)

            if len(dates) >= 2:
                today_close = float(ts[dates[0]]["4. close"])
                prev_close = float(ts[dates[1]]["4. close"])
                change_pct = (today_close - prev_close) / prev_close * 100
                color = "green" if change_pct >= 0 else "red"
                change_str = f"[{color}]{change_pct:+.2f}%[/{color}]"
        except Exception:
            change_str = "N/A"  # ถ้าโดน limit หรือ error ก็ให้เป็น N/A

        console.print("\n[bold green]FOREIGN EXCHANGE INFO[/bold green]\n")

        # หัวข้อด้านบน
        title_table = Table(show_header=False, box=None)
        title_table.add_column(justify="center", style="bold magenta")
        title_table.add_row("💵 FX SUMMARY")
        console.print(title_table)

        # ตารางหลัก
        table = Table(
            box=box.SQUARE,      
            show_header=False,
            expand=False,         
            padding=(0, 2),
        )

        table.add_column("Metric", justify="left", style="cyan", no_wrap=True)
        table.add_column("Value", justify="right", style="white", no_wrap=True)

        table.add_row("🌍 From", f"  1 {from_currency} ({from_name})".strip())
        table.add_row("🎯 To", f" {to_currency} ({to_name})".strip())
        table.add_row("💰 Rate", f"{rate:.4f}")
        table.add_row("📊 Change (1d)", change_str)
        table.add_row("🕒 Updated", last_refreshed)

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error fetching forex data: {e}[/red]")



# ดูบันทึกรายการที่บันทึกไว้
@app.command()
def watchlist(
    action: str = typer.Argument(
        ...,
        metavar="add / remove / show", 
        help="Choose one of the following:\n\n"
             "1. add: Add stock to watchlist.\n\n"
             "2. remove: Remove stock from watchlist.\n\n"
             "3. show: Show your watchlist."
    ),
    symbol: str = typer.Argument(
        None,
        help='Stock symbol, e.g AAPL NVDA.')
):
    """
    [Watchlist] add / remove / show your favorite stocks.
    """
    symbols = load_watchlist()
    action = action.lower()

    # SHOW
    if action == "show":
        if not symbols:
            console.print("[yellow]Watchlist empty[/yellow]")
            return

        api_key = os.getenv("ALPHA_VANTAGE_KEY")
        if not api_key:
            console.print("[red]Missing ALPHA_VANTAGE_KEY[/red]")
            return

        table = Table(title="Watchlist (Latest Prices)")
        table.add_column("Symbol", style="cyan")
        table.add_column("Price", justify="right")
        table.add_column("Change", justify="right")
        table.add_column("Change %", justify="right")
        table.add_column("Prev Close", justify="right")
        table.add_column("Status")

        summary = []  # เก็บไว้หาว่าตัวไหนบวก/ลบสุด

        for sym in symbols:
            url = "https://www.alphavantage.co/query"
            resp = requests.get(url, params={
                "function": "GLOBAL_QUOTE",
                "symbol": sym,
                "apikey": api_key,
            }).json().get("Global Quote", {})

            if not resp:
                table.add_row(sym, "N/A", "N/A", "N/A", "N/A", "[red]No data[/red]")
                continue

            try:
                price = float(resp["05. price"])
                change = float(resp["09. change"])
                pct = resp["10. change percent"]
                prev_close = float(resp.get("08. previous close", 0.0))
            except (KeyError, ValueError):
                table.add_row(sym, "N/A", "N/A", "N/A", "N/A", "[red]Parse error[/red]")
                continue

            color = "green" if change >= 0 else "red"
            arrow = "📈" if change >= 0 else "📉"

            price_str = f"${price:,.2f}"
            change_str = f"[{color}]{change:+.2f}[/{color}]"
            pct_str = f"[{color}]{pct}[/{color}]"
            prev_close_str = f"${prev_close:,.2f}"
            status_str = f"[{color}]{arrow} {'UP' if change >= 0 else 'DOWN'}[/{color}]"

            table.add_row(sym, price_str, change_str, pct_str, prev_close_str, status_str)

            summary.append({
                "symbol": sym,
                "change": change,
                "pct": pct,
            })

        console.print(table)

        if summary:
            best = max(summary, key=lambda x: x["change"])
            worst = min(summary, key=lambda x: x["change"])
            console.print(
                f"\n[bold]Top Gainer:[/bold] [green]{best['symbol']}[/green] ({best['change']:+.2f}, {best['pct']})"
            )
            console.print(
                f"[bold]Top Loser:[/bold] [red]{worst['symbol']}[/red] ({worst['change']:+.2f}, {worst['pct']})\n"
            )
        return


    # ADD / REMOVE
    if symbol is None:
        console.print("[red]Symbol required[/red]")
        return

    symbol = symbol.upper()

    if action == "add":
        if symbol in symbols:
            console.print("[yellow]Already exists[/yellow]")
            return
        symbols.append(symbol)
        save_watchlist(symbols)
        console.print(f"[green]Added {symbol}[/green]")
        return

    if action == "remove":
        if symbol not in symbols:
            console.print("[red]Not found[/red]")
            return
        symbols.remove(symbol)
        save_watchlist(symbols)
        console.print(f"[green]Removed {symbol}[/green]")
        return

    console.print("[red]Action must be: add/remove/show[/red]")
    
# ฟีเจอร์: ค้นหาข่าว (NewsAPI) + ลิงก์ไป X (Twitter)
@app.command()
def search(keyword: str):
    """
    [News] Search news by keyword AND generate X (Twitter) search link.
    Example: python app.py search "Elon Musk"
    """
    # ส่วนที่ 1: สร้างลิงก์ไป X (Twitter)
    x_url = f"https://twitter.com/search?q={keyword}&src=typed_query&f=live"
    console.print(f"\n[bold blue]🐦 Want to see real-time tweets?[/bold blue]")
    console.print(f"Click here 👉 [link={x_url}]Open X (Twitter) Search for '{keyword}'[/link]\n")
    console.print(f"[dim](Note: X API requires $100/mo for direct integration, using direct link instead)[/dim]\n")

    # ส่วนที่ 2: ค้นหาข่าวจาก NewsAPI (เหมือนเดิม)
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        console.print("[red]Error: NEWS_API_KEY not found in .env[/red]")
        return

    console.print(f"[yellow]🔍 Searching global news for: '{keyword}'...[/yellow]")
    url = f"https://newsapi.org/v2/everything?q={keyword}&sortBy=publishedAt&language=en&apiKey={api_key}"

    try:
        response = requests.get(url).json()
        articles = response.get("articles", [])

        if not articles:
            console.print(f"[red]No news found for '{keyword}'.[/red]")
            return

        table = Table(title=f"News Results: {keyword}")
        table.add_column("Source", style="cyan", width=15)
        table.add_column("Title & Link", style="white")

        for article in articles[:5]:
            source = article['source']['name']
            title = article['title']
            link = article['url']
            display_text = f"[link={link}]{title}[/link]\n[dim blue]🔗 {link}[/dim blue]"
            table.add_row(source, display_text)
            table.add_section()

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error searching news: {e}[/red]")
        
@app.command()
def overview(symbol: str):
    """
    [Stock] Get company fundamental data (PE, Dividend, Sector).
    Example: python app.py overview AAPL
    """
    api_key = os.getenv("ALPHA_VANTAGE_KEY")
    if not api_key:
        console.print("[red]Error: ALPHA_VANTAGE_KEY not found[/red]")
        return

    symbol = symbol.upper()
    console.print(f"[yellow]Fetching overview for {symbol}...[/yellow]")
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={api_key}"

    try:
        data = requests.get(url).json()
        if not data:
            console.print(f"[red]No data found for {symbol}.[/red]")
            return

        table = Table(title=f"Company Overview: {data.get('Name', symbol)}")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Sector", data.get("Sector", "-"))
        table.add_row("Industry", data.get("Industry", "-"))
        table.add_row("PE Ratio", data.get("PERatio", "-"))
        table.add_row("Dividend Yield", f"{data.get('DividendYield', '0')}")
        table.add_row("52Week High", data.get("52WeekHigh", "-"))
        table.add_row("52Week Low", data.get("52WeekLow", "-"))

        console.print(table)
        console.print(f"\n[dim]{data.get('Description', '')[:200]}...[/dim]") # แสดงคำอธิบายสั้นๆ

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


if __name__ == "__main__":
    app()
    
