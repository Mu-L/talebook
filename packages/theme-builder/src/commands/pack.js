import { existsSync, createWriteStream } from 'node:fs';
import { resolve, join, dirname, basename } from 'node:path';
import { readdir, stat, readFile, copyFile, mkdir, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { deflateRaw } from 'node:zlib';
import { Writable } from 'node:stream';

/**
 * Recursively collect relative file paths from a directory.
 */
async function collectFiles(dir, baseDir = dir) {
    const files = [];
    const entries = await readdir(dir);
    for (const entry of entries) {
        const fullPath = resolve(dir, entry);
        const s = await stat(fullPath);
        if (s.isDirectory()) {
            const sub = await collectFiles(fullPath, baseDir);
            files.push(...sub);
        } else {
            files.push(fullPath.slice(baseDir.length + 1).replace(/\\/g, '/'));
        }
    }
    return files;
}

/**
 * CRC32 lookup table (lazy-initialized).
 */
const CRC32_TABLE = (() => {
    const table = [];
    for (let i = 0; i < 256; i++) {
        let c = i;
        for (let j = 0; j < 8; j++) {
            c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
        }
        table[i] = c;
    }
    return table;
})();

function crc32(buf) {
    let crc = 0xFFFFFFFF;
    for (let i = 0; i < buf.length; i++) {
        crc = (crc >>> 8) ^ CRC32_TABLE[(crc ^ buf[i]) & 0xFF];
    }
    return (crc ^ 0xFFFFFFFF) >>> 0;
}

/**
 * Create a ZIP archive from a directory using only Node.js built-in modules.
 * Structure: local file headers + compressed data + central directory + EOCD.
 */
async function createZipFromDir(sourceDir, outputPath) {
    const files = await collectFiles(sourceDir, sourceDir);
    if (files.length === 0) {
        throw new Error('No files found to pack');
    }

    // Read and compress all files
    const fileData = [];
    for (const relPath of files) {
        const content = await readFile(resolve(sourceDir, relPath));
        const compressed = await new Promise((resolve, reject) => {
            deflateRaw(content, (err, result) => {
                if (err) reject(err);
                else resolve(result);
            });
        });
        fileData.push({
            name: relPath,
            content,
            compressed,
            crc: crc32(content),
        });
    }

    // Write ZIP to file
    const out = createWriteStream(outputPath);

    let offset = 0;
    const centralEntries = [];

    // Write local file headers + compressed data
    for (const file of fileData) {
        const nameBytes = Buffer.from(file.name, 'utf8');
        const header = Buffer.alloc(30 + nameBytes.length);
        let pos = 0;
        header.writeUInt32LE(0x04034b50, pos); pos += 4;  // local file header signature
        header.writeUInt16LE(20, pos); pos += 2;           // version needed to extract
        header.writeUInt16LE(0x800, pos); pos += 2;        // general purpose bit flag (UTF-8 name)
        header.writeUInt16LE(8, pos); pos += 2;            // compression method (deflate)
        header.writeUInt16LE(0, pos); pos += 2;            // last mod file time
        header.writeUInt16LE(0, pos); pos += 2;            // last mod file date
        header.writeUInt32LE(file.crc, pos); pos += 4;     // CRC-32
        header.writeUInt32LE(file.compressed.length, pos); pos += 4;  // compressed size
        header.writeUInt32LE(file.content.length, pos); pos += 4;     // uncompressed size
        header.writeUInt16LE(nameBytes.length, pos); pos += 2;        // file name length
        header.writeUInt16LE(0, pos); pos += 2;               // extra field length
        nameBytes.copy(header, pos);

        out.write(header);
        out.write(file.compressed);

        centralEntries.push({
            nameBytes,
            crc: file.crc,
            compressedSize: file.compressed.length,
            uncompressedSize: file.content.length,
            localHeaderOffset: offset,
        });

        offset += 30 + nameBytes.length + file.compressed.length;
    }

    const centralDirStart = offset;

    // Write central directory
    for (const entry of centralEntries) {
        const header = Buffer.alloc(46 + entry.nameBytes.length);
        let pos = 0;
        header.writeUInt32LE(0x02014b50, pos); pos += 4;   // central file header signature
        header.writeUInt16LE(20, pos); pos += 2;            // version made by
        header.writeUInt16LE(20, pos); pos += 2;            // version needed to extract
        header.writeUInt16LE(0x800, pos); pos += 2;         // general purpose bit flag (UTF-8 name)
        header.writeUInt16LE(8, pos); pos += 2;             // compression method
        header.writeUInt16LE(0, pos); pos += 2;             // last mod file time
        header.writeUInt16LE(0, pos); pos += 2;             // last mod file date
        header.writeUInt32LE(entry.crc, pos); pos += 4;     // CRC-32
        header.writeUInt32LE(entry.compressedSize, pos); pos += 4;  // compressed size
        header.writeUInt32LE(entry.uncompressedSize, pos); pos += 4; // uncompressed size
        header.writeUInt16LE(entry.nameBytes.length, pos); pos += 2; // file name length
        header.writeUInt16LE(0, pos); pos += 2;             // extra field length
        header.writeUInt16LE(0, pos); pos += 2;             // file comment length
        header.writeUInt16LE(0, pos); pos += 2;             // disk number start
        header.writeUInt16LE(0, pos); pos += 2;             // internal file attributes
        header.writeUInt32LE(0, pos); pos += 4;             // external file attributes
        header.writeUInt32LE(entry.localHeaderOffset, pos); pos += 4; // relative offset of local header
        entry.nameBytes.copy(header, pos);

        out.write(header);
        offset += 46 + entry.nameBytes.length;
    }

    // Write end of central directory record
    const eocd = Buffer.alloc(22);
    let pos = 0;
    eocd.writeUInt32LE(0x06054b50, pos); pos += 4;           // end of central dir signature
    eocd.writeUInt16LE(0, pos); pos += 2;                    // number of this disk
    eocd.writeUInt16LE(0, pos); pos += 2;                    // disk where central directory starts
    eocd.writeUInt16LE(centralEntries.length, pos); pos += 2; // number of central directory records on this disk
    eocd.writeUInt16LE(centralEntries.length, pos); pos += 2; // total number of central directory records
    eocd.writeUInt32LE(offset - centralDirStart, pos); pos += 4; // size of central directory
    eocd.writeUInt32LE(centralDirStart, pos); pos += 4;      // offset of start of central directory
    eocd.writeUInt16LE(0, pos);                              // comment length

    out.write(eocd);
    out.end();

    await new Promise((resolve, reject) => {
        out.on('finish', resolve);
        out.on('error', reject);
    });
}

export async function packCommand(options) {
    const projectDir = resolve(options.dir || '.');
    const componentsDir = resolve(projectDir, options.outDir || 'components');
    const themeJsonPath = resolve(projectDir, 'theme.json');

    // Validate prerequisites
    if (!existsSync(themeJsonPath)) {
        console.error('ERROR: theme.json not found. Run inside a theme project directory.');
        process.exit(1);
    }

    if (!existsSync(componentsDir)) {
        console.error('ERROR: components/ directory not found. Run "theme-builder build" first.');
        process.exit(1);
    }

    // Read theme name from theme.json
    const themeJson = JSON.parse(await readFile(themeJsonPath, 'utf-8'));
    const themeName = themeJson.name;
    if (!themeName) {
        console.error('ERROR: theme.json missing "name" field.');
        process.exit(1);
    }

    const distDir = resolve(projectDir, 'dist');
    await mkdir(distDir, { recursive: true });
    const outputPath = resolve(distDir, `${themeName}.zip`);

    console.log(`Packing theme "${themeName}" into ${outputPath} ...`);

    // Create temporary directory with correct ZIP structure:
    //   theme.zip
    //   ├── theme.json
    //   └── components/
    //       ├── AppHeader.js
    //       ├── AppFooter.js
    //       └── ...
    const tmpDir = join(tmpdir(), `theme-pack-${Date.now()}-${Math.random().toString(36).slice(2)}`);

    try {
        await mkdir(tmpDir, { recursive: true });

        // Copy theme.json to root
        await copyFile(themeJsonPath, join(tmpDir, 'theme.json'));

        // Copy components/ directory
        const destComponentsDir = join(tmpDir, 'components');
        await mkdir(destComponentsDir, { recursive: true });

        const compFiles = await collectFiles(componentsDir, componentsDir);
        for (const relPath of compFiles) {
            const destPath = join(destComponentsDir, relPath);
            await mkdir(dirname(destPath), { recursive: true });
            await copyFile(join(componentsDir, relPath), destPath);
        }

        // Pack the temporary directory into ZIP
        const tmpFiles = await collectFiles(tmpDir, tmpDir);
        await createZipFromDir(tmpDir, outputPath);

        const s = await stat(outputPath);
        console.log(`\n✓ Theme packed: ${outputPath} (${(s.size / 1024).toFixed(1)} KB)`);
        console.log(`  ${tmpFiles.length} files included.`);
    } finally {
        await rm(tmpDir, { recursive: true, force: true });
    }
}
