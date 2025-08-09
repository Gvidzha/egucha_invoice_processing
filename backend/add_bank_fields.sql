-- Pievieno jaunos piegādātāja bankas laukus
-- Palaidiet šo SQL datubāzē manuāli

-- Pārbaudam vai lauki jau eksistē
DO $$
BEGIN
    -- Pievienojam supplier_bank_name ja neeksistē
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'invoices' AND column_name = 'supplier_bank_name'
    ) THEN
        ALTER TABLE invoices ADD COLUMN supplier_bank_name VARCHAR(255);
        RAISE NOTICE 'Pievienots lauks: supplier_bank_name';
    ELSE
        RAISE NOTICE 'Lauks supplier_bank_name jau eksistē';
    END IF;
    
    -- Pievienojam supplier_swift_code ja neeksistē  
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'invoices' AND column_name = 'supplier_swift_code'
    ) THEN
        ALTER TABLE invoices ADD COLUMN supplier_swift_code VARCHAR(20);
        RAISE NOTICE 'Pievienots lauks: supplier_swift_code';
    ELSE
        RAISE NOTICE 'Lauks supplier_swift_code jau eksistē';
    END IF;
END $$;

-- Pārbaudam vai lauki ir pievienoti
SELECT column_name, data_type, character_maximum_length
FROM information_schema.columns 
WHERE table_name = 'invoices' 
AND column_name IN ('supplier_bank_name', 'supplier_swift_code')
ORDER BY column_name;
