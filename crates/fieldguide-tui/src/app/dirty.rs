bitflags::bitflags! {
    #[derive(Default, Debug, Clone, Copy, PartialEq, Eq)]
    pub struct Dirty: u8 {
        const NONE      = 0;
        const LAYOUT    = 1 << 0;
        const DATA      = 1 << 1;
        const HIGHLIGHT = 1 << 2;
        const STATUS    = 1 << 3;
        const ALL       = Self::LAYOUT.bits() | Self::DATA.bits() | Self::HIGHLIGHT.bits() | Self::STATUS.bits();
    }
}
