
import { test, expect } from '@playwright/test';

test.describe('WebDAV Readme Page', () => {
    test.beforeEach(async ({ request }) => {
        await request.post('http://127.0.0.1:8080/_test/reset', {
            data: { installed: true }
        });
    });

    test('displays WebDAV connection guide', async ({ page }) => {
        await page.goto('/webdav-readme');

        await expect(page.getByRole('heading', { name: 'WebDAV 介绍' })).toBeVisible();
        await expect(page.getByText('您的 WebDAV 地址为：')).toBeVisible();
        await expect(page.getByText('WebDAV 介绍')).toHaveCount(1);

        // 应包含常见客户端与配置步骤
        await expect(page.getByText('常见 WebDAV 客户端')).toBeVisible();
        await expect(page.getByText('配置指南')).toBeVisible();
    });

    test('shows WebDAV link on the OPDS readme page', async ({ page }) => {
        await page.goto('/opds-readme');

        const webdavLink = page.getByRole('link', { name: 'WebDAV 介绍' });
        await expect(webdavLink).toBeVisible();
        await expect(webdavLink).toHaveAttribute('href', '/webdav-readme');
    });
});
