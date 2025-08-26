"""Notifications router for Telegram notifications."""

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from ..dependencies import require_telegram_config
from ..schemas import APIResponse, NotificationRequest

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("/test", response_model=APIResponse)
async def test_notification(
    notification: NotificationRequest,
    telegram_config: tuple[str, str] = Depends(require_telegram_config)
) -> APIResponse:
    """Send a test notification via Telegram."""
    bot_token, chat_id = telegram_config
    
    try:
        # Send message via Telegram Bot API
        message = f"🔔 **Test Notification**\n\n{notification.message}\n\nType: {notification.notification_type}"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "Markdown"
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    return APIResponse(
                        success=True,
                        message="Test notification sent successfully"
                    )
                else:
                    return APIResponse(
                        success=False,
                        error=f"Telegram API error: {result.get('description', 'Unknown error')}"
                    )
            else:
                return APIResponse(
                    success=False,
                    error=f"HTTP error {response.status_code}: {response.text}"
                )
                
    except Exception as e:
        return APIResponse(
            success=False,
            error=f"Failed to send notification: {str(e)}"
        )


@router.post("/signal", response_model=APIResponse)
async def send_signal_notification(
    signal_data: dict,
    telegram_config: tuple[str, str] = Depends(require_telegram_config)
) -> APIResponse:
    """Send a signal notification via Telegram."""
    bot_token, chat_id = telegram_config
    
    try:
        # Format signal message
        side_emoji = "🟢" if signal_data.get("side") == "buy" else "🔴"
        confidence = signal_data.get("confidence", 0)
        confidence_emoji = "🔥" if confidence > 0.8 else "⚡" if confidence > 0.6 else "📊"
        
        message = f"""
{side_emoji} **New Trading Signal** {confidence_emoji}

**Pair:** {signal_data.get('pair', 'N/A')}
**Side:** {signal_data.get('side', 'N/A').upper()}
**Entry:** {signal_data.get('entry_price', 'N/A')}
**Stop Loss:** {signal_data.get('stop_loss', 'N/A')}
**Take Profit:** {signal_data.get('take_profit', 'N/A')}
**Confidence:** {confidence:.1%}
**Strategy:** {signal_data.get('strategy', 'N/A')}
**Timeframe:** {signal_data.get('timeframe', 'N/A')}

⏰ {signal_data.get('timestamp', 'N/A')}
        """.strip()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "Markdown"
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    return APIResponse(
                        success=True,
                        message="Signal notification sent successfully"
                    )
                else:
                    return APIResponse(
                        success=False,
                        error=f"Telegram API error: {result.get('description', 'Unknown error')}"
                    )
            else:
                return APIResponse(
                    success=False,
                    error=f"HTTP error {response.status_code}: {response.text}"
                )
                
    except Exception as e:
        return APIResponse(
            success=False,
            error=f"Failed to send signal notification: {str(e)}"
        )


@router.post("/backtest", response_model=APIResponse)
async def send_backtest_notification(
    backtest_data: dict,
    telegram_config: tuple[str, str] = Depends(require_telegram_config)
) -> APIResponse:
    """Send a backtest completion notification via Telegram."""
    bot_token, chat_id = telegram_config
    
    try:
        # Format backtest message
        total_return = backtest_data.get("total_return", 0)
        return_emoji = "📈" if total_return > 0 else "📉"
        win_rate = backtest_data.get("win_rate", 0)
        win_rate_emoji = "🎯" if win_rate > 60 else "🎲"
        
        message = f"""
{return_emoji} **Backtest Completed** {win_rate_emoji}

**Pair:** {backtest_data.get('pair', 'N/A')}
**Strategy:** {backtest_data.get('strategy', 'N/A')}
**Timeframe:** {backtest_data.get('timeframe', 'N/A')}
**Period:** {backtest_data.get('start_date', 'N/A')} - {backtest_data.get('end_date', 'N/A')}

**Results:**
• Total Return: {total_return:.2f}%
• Win Rate: {win_rate:.1f}%
• Total Trades: {backtest_data.get('total_trades', 'N/A')}
• Max Drawdown: {backtest_data.get('max_drawdown', 'N/A'):.2f}%
• Sharpe Ratio: {backtest_data.get('sharpe_ratio', 'N/A'):.2f}

💰 Initial Capital: ${backtest_data.get('initial_capital', 'N/A'):,.2f}
💵 Final Capital: ${backtest_data.get('final_capital', 'N/A'):,.2f}
        """.strip()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "Markdown"
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    return APIResponse(
                        success=True,
                        message="Backtest notification sent successfully"
                    )
                else:
                    return APIResponse(
                        success=False,
                        error=f"Telegram API error: {result.get('description', 'Unknown error')}"
                    )
            else:
                return APIResponse(
                    success=False,
                    error=f"HTTP error {response.status_code}: {response.text}"
                )
                
    except Exception as e:
        return APIResponse(
            success=False,
            error=f"Failed to send backtest notification: {str(e)}"
        )


@router.post("/alert", response_model=APIResponse)
async def send_alert_notification(
    alert_data: dict,
    telegram_config: tuple[str, str] = Depends(require_telegram_config)
) -> APIResponse:
    """Send a general alert notification via Telegram."""
    bot_token, chat_id = telegram_config
    
    try:
        # Format alert message
        alert_type = alert_data.get("type", "info")
        type_emoji = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "🚨",
            "success": "✅"
        }.get(alert_type, "ℹ️")
        
        message = f"""
{type_emoji} **Alert: {alert_data.get('title', 'System Alert')}**

{alert_data.get('message', 'No message provided')}

**Details:**
{alert_data.get('details', 'No additional details')}

⏰ {alert_data.get('timestamp', 'N/A')}
        """.strip()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "Markdown"
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    return APIResponse(
                        success=True,
                        message="Alert notification sent successfully"
                    )
                else:
                    return APIResponse(
                        success=False,
                        error=f"Telegram API error: {result.get('description', 'Unknown error')}"
                    )
            else:
                return APIResponse(
                    success=False,
                    error=f"HTTP error {response.status_code}: {response.text}"
                )
                
    except Exception as e:
        return APIResponse(
            success=False,
            error=f"Failed to send alert notification: {str(e)}"
        )


@router.get("/status")
async def get_notification_status(
    telegram_config: tuple[str, str] = Depends(require_telegram_config)
):
    """Get notification system status."""
    bot_token, chat_id = telegram_config
    
    try:
        # Test Telegram bot connection
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.telegram.org/bot{bot_token}/getMe",
                timeout=5.0
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    bot_info = result.get("result", {})
                    return {
                        "status": "connected",
                        "bot_name": bot_info.get("first_name", "Unknown"),
                        "bot_username": bot_info.get("username", "Unknown"),
                        "chat_id": chat_id,
                        "last_test": "Now"
                    }
                else:
                    return {
                        "status": "error",
                        "error": result.get("description", "Unknown error"),
                        "chat_id": chat_id
                    }
            else:
                return {
                    "status": "error",
                    "error": f"HTTP error {response.status_code}",
                    "chat_id": chat_id
                }
                
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "chat_id": chat_id
        }
