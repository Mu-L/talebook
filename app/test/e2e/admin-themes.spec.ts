import { test, expect } from '@playwright/test';

test.describe('Admin Themes', () => {
    test.beforeEach(async ({ request }) => {
        await request.post('http://127.0.0.1:8080/_test/reset', {
            data: { installed: true }
        });
    });

    test('activating a theme updates the card without refetching the list', async ({ page }) => {
        await page.goto('/admin/themes');

        // 内置主题卡片（mock 无 display_name，卡片标题回退显示 name）
        const card = page.locator('.theme-card', { hasText: 'graphite' });
        await expect(card).toBeVisible();
        await expect(card.getByRole('button', { name: '激活', exact: true })).toBeVisible();

        // 激活会触发服务器自动重启；统计点击后是否又发起 GET /api/themes（列表接口）
        let listRefetchAfterClick = 0;
        let clicked = false;
        page.on('request', (req) => {
            if (!clicked) return;
            const { pathname } = new URL(req.url());
            if (req.method() === 'GET' && pathname === '/api/themes') {
                listRefetchAfterClick += 1;
            }
        });

        clicked = true;
        await card.getByRole('button', { name: '激活', exact: true }).click();

        // 卡片本地翻转为已激活状态
        await expect(card.getByText('已激活')).toBeVisible();

        // 关键断言：激活后没有再次拉取主题列表，避免撞上重启窗口
        await page.waitForTimeout(500);
        expect(listRefetchAfterClick).toBe(0);
    });
});
