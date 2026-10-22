package com.nstut.repair.core;

import java.io.*;
import java.util.*;

public final class RepairSettings {
    public final int capacity, energyPerPoint, pointsPerTick;
    private final Set<String> blacklist, whitelist;

    public RepairSettings(int capacity, int energyPerPoint, int pointsPerTick, Set<String> blacklist, Set<String> whitelist) {
        if (capacity < 1 || energyPerPoint < 1 || energyPerPoint > capacity || pointsPerTick < 1) {
            throw new IllegalArgumentException("Require capacity >= energyPerPoint >= 1 and pointsPerTick >= 1");
        }
        this.capacity = capacity;
        this.energyPerPoint = energyPerPoint;
        this.pointsPerTick = pointsPerTick;
        this.blacklist = Collections.unmodifiableSet(new HashSet<String>(blacklist));
        this.whitelist = Collections.unmodifiableSet(new HashSet<String>(whitelist));
    }
    public boolean allows(String id) { return !blacklist.contains(id) && (whitelist.isEmpty() || whitelist.contains(id)); }
    public static RepairSettings defaults() {
        return new RepairSettings(100000, 100, 1, Collections.<String>emptySet(), Collections.<String>emptySet());
    }
    private static Set<String> ids(String value) {
        Set<String> result = new HashSet<String>();
        for (String id : value.split(",")) if (!id.trim().isEmpty()) result.add(id.trim());
        return result;
    }
    public static RepairSettings load(File file) {
        Properties p = new Properties();
        p.setProperty("capacity", "100000");
        p.setProperty("energyPerPoint", "100");
        p.setProperty("pointsPerTick", "1");
        p.setProperty("blacklist", "");
        p.setProperty("whitelist", "");
        try {
            if (file.isFile()) { try (InputStream in = new FileInputStream(file)) { p.load(in); } }
            RepairSettings settings = new RepairSettings(Integer.parseInt(p.getProperty("capacity")),
                Integer.parseInt(p.getProperty("energyPerPoint")), Integer.parseInt(p.getProperty("pointsPerTick")),
                ids(p.getProperty("blacklist")), ids(p.getProperty("whitelist")));
            if (!file.exists()) {
                File parent = file.getAbsoluteFile().getParentFile();
                if (!parent.isDirectory() && !parent.mkdirs()) throw new IOException("Cannot create " + parent);
                try (OutputStream out = new FileOutputStream(file)) { p.store(out, "Powered repair settings. Restart to apply. Comma-separated item IDs; blacklist takes priority."); }
            }
            return settings;
        } catch (IOException | IllegalArgumentException e) {
            throw new IllegalStateException("Invalid repair configuration: " + file, e);
        }
    }
}
