package mn.csm311.lab12.task3;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.NoSuchFileException;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.Map;

/**
 * Энгийн key=value файлын уншигч.
 *
 * ДААЛГАВАР 3: Доорх хэрэгжилтэд хэд хэдэн алдаа зохицуулалтын асуудал бий:
 *
 *  Асуудал A: Exception-ыг залгиж (swallow) байна — эвдэрсэн файл чимээгүй
 *             хоосон AppConfig буцаана. Үүнээс үйлдвэрт ямар ч log үлдэхгүй.
 *  Асуудал B: Reader-ыг хуучин try/finally-гүй хаалгаар хаадаг — exception
 *             гарвал close() хийгдэхгүй, resource leak үүснэ.
 *  Асуудал C: IOException нь дотоод API-гийн дэлгэрэнгүй. Дуудлагч ACК
 *             IOException-ыг catch хийх шаардлагагүй. Үүнийг translation
 *             хийж ConfigLoadException болгон гаргах хэрэгтэй.
 *  Асуудал D: NoSuchFileException нь IOException-ийн тусгай төрөл.
 *             Үүнийг тодорхой тайлбартайгаар мэдээлэх хэрэгтэй.
 *
 * Таны даалгавар: Доорх load() аргыг дараах шаардлагаар дахин бич:
 *
 *  1. try-with-resources ашиглан Reader-ыг автоматаар хаах.
 *  2. NoSuchFileException-ыг тусад нь барьж, "config file not found: <path>"
 *     гэсэн мессежтэй ConfigLoadException шид.
 *  3. Бусад IOException-ыг барьж, "failed to read config: <path>" гэсэн
 *     мессежтэй ConfigLoadException болгон wrap & rethrow хий
 *     (cause-ыг алдалгүй дамжуул).
 *  4. path null бол IllegalArgumentException шид (fail-fast).
 */
public class FileConfigLoader {

    public AppConfig load(Path path) {
        // TODO 3.1: path null бол fail-fast
        if (path == null) throw new IllegalArgumentException();
        Map<String, String> props = new HashMap<>();

        // TODO 3.2: Доорх блокыг try-with-resources, ConfigLoadException
        //           зохих exception translation-той болгон дахин бич.
        BufferedReader reader = null;
        try (BufferedReader r = Files.newBufferedReader(path))  {
            reader = new BufferedReader(new FileReader(path.toFile()));
            String line;
            while ((line = reader.readLine()) != null) {
                parseLine(line, props);
            }
        } catch (NoSuchFileException e) {
    throw new ConfigLoadException("config file not found", e);
} catch (IOException e) {
    throw new ConfigLoadException("failed to read config: " + path, e);
} finally {
            // Асуудал B: close() ч бас throw хийж магадгүй
            if (reader != null) {
                try { reader.close(); } catch (IOException e) { /* залгих */ }
            }
        }

        return new AppConfig(props);
    }

    private void parseLine(String line, Map<String, String> props) {
        line = line.trim();
        if (line.isEmpty() || line.startsWith("#")) return;
        int eq = line.indexOf('=');
        if (eq <= 0) return;
        String key = line.substring(0, eq).trim();
        String value = line.substring(eq + 1).trim();
        props.put(key, value);
    }
}
